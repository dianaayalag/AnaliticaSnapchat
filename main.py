# Requirements:

import cv2 # OpenCV para procesamiento de imágenes
import threading # Threading para paralelizar las tareas
import os # OS para interactuar con el sistema operativo
import time # Time para manejar tareas en función del tiempo

from tkinter import * # TKinter para interfaz gráfica
from PIL import Image # PIL para representar imágenes
from PIL import ImageTk # PIL para modificar imágenes con Tkintwe
from threading import Thread # Thread es el constructor de hilos
from os import listdir # listdir para lista el directorio
from os.path import isfile, join # para procesar archivos

# Función para escoger el sprite que se necesita
def put_sprite(num):
    global SPRITES, BTNS
    SPRITES[num] = (1 - SPRITES[num])
    if SPRITES[num]:
        BTNS[num].config(relief=SUNKEN)
    else:
        BTNS[num].config(relief=RAISED)

# Dibuja el sprite sobre el frame
# Mediante el alpha channel se reemplazan los pixeles
def draw_sprite(frame, sprite, x_offset, y_offset):
    (h,w) = (sprite.shape[0], sprite.shape[1])
    (imgH,imgW) = (frame.shape[0], frame.shape[1])
    # Condicionales por si el sprite sale de la imagen
    if y_offset+h >= imgH:
        sprite = sprite[0:imgH-y_offset,:,:]

    if x_offset+w >= imgW:
        sprite = sprite[:,0:imgW-x_offset,:]

    if x_offset < 0:
        sprite = sprite[:,abs(x_offset)::,:]
        w = sprite.shape[1]
        x_offset = 0

    # para cada canal RGB
    for c in range(3):
            frame[int(y_offset):int(y_offset+h), int(x_offset):int(x_offset+w), c] =  \
            sprite[:,:,c] * (sprite[:,:,3]/255.0) +  frame[int(y_offset):int(y_offset+h), int(x_offset):int(x_offset+w), c] * (1.0 - sprite[:,:,3]/255.0)
    return frame


# Rectángulos
def apply_Haar_filter(img, haar_cascade,scaleFact = 1.1, minNeigh = 5, minSizeW = 30):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    features = haar_cascade.detectMultiScale(
        gray,
        scaleFactor=scaleFact,
        minNeighbors=minNeigh,
        minSize=(minSizeW, minSizeW),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    return features


# Ajustar el sprite al tamaño de la cabeza, recortarlo si sale de la imagen
def adjust_sprite2head(sprite, head_width, head_ypos):
    (h_sprite,w_sprite) = (sprite.shape[0], sprite.shape[1])
    factor = 1.0*head_width/w_sprite
    sprite = cv2.resize(sprite, (0,0), fx=factor, fy=factor)
    (h_sprite,w_sprite) = (sprite.shape[0], sprite.shape[1])
    y_orig =  head_ypos-h_sprite
    if (y_orig < 0):
            sprite = sprite[abs(y_orig)::,:,:] #recortar sprite
            y_orig = 0
    return (sprite, y_orig)


def apply_sprite(image, path2sprite,w,x,y):
    sprite = cv2.imread(path2sprite,-1)
    (sprite, y_final) = adjust_sprite2head(sprite, w, y)
    image = draw_sprite(image,sprite,x, y_final)


def apply_sprite2feature(image, sprite_path, haar_filter, x_offset, y_offset, y_offset_image, adjust2feature, desired_width, x, y, w, h):
    sprite = cv2.imread(sprite_path,-1)
    (h_sprite,w_sprite) = (sprite.shape[0], sprite.shape[1])
    xpos = x + x_offset
    ypos = y + y_offset
    factor = 1.0*desired_width/w_sprite
    sub_img = image[int(y + y_offset_image):y+h,x:x+w,:]

    feature = apply_Haar_filter(sub_img, haar_filter, 1.3 , 10, 10)
    if len(feature)!=0:
        xpos, ypos = x, y + feature[0,1] # Ajustar features en y

        if adjust2feature:
            size_mustache = 1.2 # ratio del tamaño del bigote
            factor = 1.0*(feature[0,2]*size_mustache)/w_sprite
            xpos =  x + feature[0,0] - int(feature[0,2]*(size_mustache-1)/2) # imagen centrada
            ypos = y + y_offset_image + feature[0,1] - int(h_sprite*factor)

    sprite = cv2.resize(sprite, (0,0), fx=factor, fy=factor)
    image = draw_sprite(image,sprite,xpos,ypos)

# Evento principal - OpenCV
def cvloop(run_event):
    global panelA
    global SPRITES

    dir_ = "./sprites/ullogo/"
    ulima = [f for f in listdir(dir_) if isfile(join(dir_, f))] #Imágenes del logo UL para la animación
    i = 0
    video_capture = cv2.VideoCapture(0) # capturar imágenes de la cámara web
    (x,y,w,h) = (0,0,10,10)

    #Información de los filtros
    haar_faces = cv2.CascadeClassifier('./filters/haarcascade_frontalface_default.xml')
    haar_eyes = cv2.CascadeClassifier('./filters/haarcascade_eye.xml')
    haar_mouth = cv2.CascadeClassifier('./filters/Mouth.xml')
    haar_nose = cv2.CascadeClassifier('./filters/Nose.xml')

    while run_event.is_set(): # Loop mientras el hilo esté activo
        ret, image = video_capture.read()

        faces = apply_Haar_filter(image, haar_faces, 1.3 , 5, 30)
        for (x,y,w,h) in faces: # Chequear si hay rostros. Si hay, tomar el primero

            # Condicional sombrero
            if SPRITES[0]:
                apply_sprite(image, "./sprites/hat.png",w,x,y)

            # Condicional bigote
            if SPRITES[1]:
                apply_sprite2feature(image, "./sprites/mustache.png", haar_mouth, w/4, 2*h/3, h/2, True, w/2, x, y, w, h)

            # Condicional lentes de sol
            if SPRITES[3]:
                apply_sprite2feature(image, "./sprites/glasses.png", haar_eyes, 0, h/3, 0, False, w, x, y, w, h)

            # Condicional logo UL
            if SPRITES[2]:
                #Las imágenes están ordenadas para que parezca una animación
                apply_sprite(image, dir_+ulima[i],w,x,y)
                i+=1
                i = 0 if i >= len(ulima) else i # loopear imágenes del folder

        # BGR a RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # Imagen usando PIL
        image = Image.fromarray(image)
        # PIL a Tkinter
        image = ImageTk.PhotoImage(image)
        # Mostrar imagen en el panel
        panelA.configure(image=image)
        panelA.image = image
    video_capture.release()

# Iniciar interfaz
root = Tk()
root.title("Filtros de Snapchat versión UL")
this_dir = os.path.dirname(os.path.realpath(__file__))
# Colocar logo de la UL como icon
imgicon = PhotoImage(file=os.path.join(this_dir,'imgs/icon2.gif'))
root.tk.call('wm', 'iconphoto', root._w, imgicon)

# Insertar los botones que asignarán los sprites
btn1 = Button(root, text="Gorro", command = lambda: put_sprite(0))
btn1.pack(side="top", fill="both", expand="no", padx="10", pady="10")

btn2 = Button(root, text="Bigote", command = lambda: put_sprite(1))
btn2.pack(side="top", fill="both", expand="no", padx="10", pady="10")

btn3 = Button(root, text="UL logo", command = lambda: put_sprite(2))
btn3.pack(side="top", fill="both", expand="no", padx="10", pady="10")

btn4 = Button(root, text="Lentes de Sol", command = lambda: put_sprite(3) )
btn4.pack(side="top", fill="both", expand="no", padx="10", pady="10")

# Create el panel de imágenes
panelA = Label(root)
panelA.pack( padx=10, pady=10)

# Control de sprites
SPRITES = [0,0,0,0] # 1 visible, 0 no visible
BTNS = [btn1, btn2, btn3, btn4]


# Crear thread
run_event = threading.Event()
run_event.set()
action = Thread(target=cvloop, args=(run_event,))
action.setDaemon(True)
action.start()


# Terminar ciclo
def terminate():
        global root, run_event, action
        print("--Cerrando el hilo de OpenCV--")
        run_event.clear()
        time.sleep(1)
        #action.join() #strangely in Linux this thread does not terminate properly, so .join never finishes
        root.destroy()
        print("Todo cerrado")
        print("Curso: Analítica Predictiva de Datos")
        print("Integrantes: Diana Ayala, Alexander Mendez, Miguel Placido, Alvaro Samanamud")

# Activar función de terminr cuando se cierra la ventana
root.protocol("WM_DELETE_WINDOW", terminate)
root.mainloop()
