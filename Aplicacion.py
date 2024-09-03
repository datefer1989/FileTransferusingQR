import tkinter as tk

from pyzbar.pyzbar import decode
import os
from os import remove
import time
import cv2
import qrcode
import hashlib
from tkinter.filedialog import askopenfilename,askdirectory 
import math

import base64

#Por defecto la versión mínima usable para la transmisión, limitada por el protocolo.
maxversion=3

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Transmisor mediante códigos QR")

        self.image = tk.PhotoImage(file="img.png")
        self.label = tk.Label(image=self.image)
        self.label.pack()

        self.button1 = tk.Button(self, text="Tx: Calibrar", command=self.on_button1_click)
        self.button1.pack()

        self.button2 = tk.Button(self, text="RX: Calibrar", command=self.on_button2_click)
        self.button2.pack()

        self.button3 = tk.Button(self, text="TX: Enviar Archivo", command=self.on_button3_click)
        self.button3.pack()
        self.button4 = tk.Button(self, text="RX: Recibir Archivo", command=self.on_button4_click)
        self.button4.pack()

        self.label2 = tk.Label(self,text="Escoja una opción")
        self.label2.pack()
        
    def on_button1_click(self):
        tinicio=time.time()
        calibrateTX()
        ttotal=time.time()-tinicio
        with open("Fichero estadisticas.txt",'w') as f:
            f.writelines("Tiempo de calibración(s): "+str(ttotal)+"\n")   

    def on_button2_click(self):
        calibrateRX()
        



    def on_button3_click(self):
        filename=selectFile()
        filename=os.path.basename(filename)
        if(len(filename)>9):
            print("El nombre del archivo tiene que ser inferior a 10.")
            exit()
        tinicio=time.time()    
        size=sendTX(maxversion,filename)
        ttotal=time.time()-tinicio
        with open("Fichero estadisticas.txt",'a') as f:
            f.writelines("#####Nueva transmisión#####"+"\n")
            f.writelines("Tiempo de transmisión(s): "+str(ttotal)+"\n")
            f.writelines("Tasa de transmisión(Bytes/s): "+str(size/ttotal)+" \n")   

    def on_button4_click(self):
        sendRX()  


def readQR(frame):
    
    detectedBarcodes = decode(frame)
    if not detectedBarcodes:  
            return None
    else: 
        # Traverse through all the detected barcodes in image 
        for barcode in detectedBarcodes:   
        
            if barcode.data!="": 
                
            # Print the barcode data 
                return barcode.data


def generateQR(datos,n_version,nombreQR):
    #Este vector genera los códigos qr ajustados al máximo tamaño que permite mi pantalla. Es necesario crearlo para cada pantalla del transmisor.
    #En caso contrario, no está controlado el tamaño del código QR en pantalla y puede provocar fallos
    size=[27,25,21,19,17,15,13,12,11,11,10,9,9,8,8,7,7,7,6,6,6,6,5,5,5,5,5,4,4,4,4,4,4,4,4,3,3,3,3,3]

    qr = qrcode.QRCode(
        version=n_version,
        error_correction=qrcode.ERROR_CORRECT_L,
        box_size=size[n_version-1],
        border=1,
    )
    qr.add_data(datos)
    qr.make(fit=True)
    img=qr.make_image(fill_color="black",black_color="white")
    img.save(nombreQR)

def showQR(img, x, y,time):
    winname="1"
    cv2.namedWindow(winname)        # Create a named window
    cv2.moveWindow(winname, x, y)   # Move it to (x,y)
    cv2.imshow(winname,img)
    cv2.waitKey(time)

def calibrateRX():
    data_ant=""
    first=True
    ntimes=0
    threshold=50
    #Se comienza la lectura de imágenes.
    capture=cv2.VideoCapture(0)
    while(capture. isOpened()):
        ret, frame = capture. read()
        data=readQR(frame)

        if data!=None:
            if(data!=data_ant):
                ntimes=0
                nqr=0
                first=False
                generateQR(data,1,"QRcalibracionRX.png")
                img=cv2.imread("QRcalibracionRX.png")
                showQR(img,0,0,1)
                nqr=nqr+1
            else:
                showQR(img,0,0,1)              
        else:
            if first:
                ntimes=ntimes+1
                time.sleep(0.5)
                if ntimes>threshold:
                    print("Transmisor no inicia.")
                    capture.release()
                    cv2.destroyAllWindows()
                    break
            else:
                showQR(img,0,0,1)
                ntimes=ntimes+1
                if ntimes>threshold:
                    print("Transmisor FIN.")
                    generateQR("Fin",1,"QRFin.png")
                    img=cv2.imread("QRFin.png")
                    showQR(img,0,0,5000)
                    capture.release()
                    cv2.destroyAllWindows()
                    remove("QRFin.png")
                    remove("QRcalibracionRX.png")
                    break

def sendRX():
    data_ant=""
    first=True
    ntimes=0
    threshold=50
    first=True
    nqr=0
    #Se comienza la lectura de imágenes.
    capture=cv2.VideoCapture(0)
    
    while(capture. isOpened()):
        ret, frame = capture. read()
        data=readQR(frame)


        if data!=None:
            if(data!=data_ant):
                if first:
                    data_ant=data
                    [hash,name_size,name,n_paq]=readHeader(data.decode())
                    print("Header:",data)
                    print("Nº de paquetes:",n_paq)
                    ntimes=0
                    first=False
                    generateQR(str(nqr),1,"QRresponseRX.png")
                    img=cv2.imread("QRresponseRX.png")
                    showQR(img,0,0,1)
                    nqr=nqr+1
                    f=open(name,'wb')
                else:
                    data_ant=data
                    ntimes=0
                    f.write(base64.b64decode(data))
                    generateQR(nqr,1,"QRresponseRX.png")
                    img=cv2.imread("QRresponseRX.png")
                    showQR(img,0,0,1)
                    #print("Respuesta nº:",str(nqr))
                    if(nqr==int(n_paq)):
                        print("Condición de fin.")
                        f.close()
                        if hash==md5(name):
                            print("El código Hash coincide. Recepción correcta.")
                            capture.release()
                            remove("QRresponseRX.png")
                            cv2.destroyAllWindows()
                            break
                        else:
                            print("Código Hash no coincide, archivo corrupto. Eliminando...")
                            remove(name.decode())
                            remove("QRresponseRX.png")
                            capture.release()
                            cv2.destroyAllWindows()
                            break
                    nqr=nqr+1
            else:
                showQR(img,0,0,1)     
        #Read None         
        else:
            if first:
                print("Esperando al TX. "+str(ntimes))
                ntimes=ntimes+1
                time.sleep(0.5)
                if ntimes>threshold:
                    print("Transmisor no inicia.")
                    capture.release()
                    cv2.destroyAllWindows()
                    break
            else:
                showQR(img,0,0,500)
                ntimes=ntimes+1
                if ntimes>threshold:
                    print("Transmisor FIN.")
                    generateQR("Fin",1,"QRFin.png")
                    img=cv2.imread("QRFin.png")
                    showQR(img,0,0,5000)
                    capture.release()
                    cv2.destroyAllWindows()
                    remove("QRFin.png")
                    f.close()
                    break

def calibrateTX():
    ntimes=0
    data_ant=""
    v=1
    threshold=50
    first=True
    #Generar el primer QR que es va a enviar.
    generateQR(str(v),v,"QRcalibracionTX.png")
    img=cv2.imread("QRcalibracionTX.png")
    showQR(img,0,0,1)
    #Se comienza la lectura de imágenes.
    capture=cv2.VideoCapture(0)
    while(capture. isOpened()):
        ret, frame = capture. read()
        
        data=readQR(frame)

        if data!=None:
            first=False
            if(data!=data_ant):
                ntimes=0
                # cv2.destroyAllWindows()
                # remove("QRcalibracionTX "+data_ant)
                data_ant=data
                if data.decode()==str(v):
                    v=v+1
                    # print("El valor de v:",v)
                    generateQR(str(v),v,"QRcalibracionTX.png")
                    img=cv2.imread("QRcalibracionTX.png")
                    showQR(img,0,0,1)
                    
                elif data.decode()=="Fin":
                    print("Fin calibración.")
                    remove("QRcalibracionTX.png")
                    capture.release()
                    cv2.destroyAllWindows()
                    break
                else:
                    ntimes=ntimes+1
                    if(ntimes>threshold):
                        print("Fin calibración.")
                        remove("QRcalibracionTX.png")
                        print("Confirmación inesperada mayor que umbral de error. Terminando")
                        capture.release()
                        cv2.destroyAllWindows()
                        break

                    print("ERROR.QR no esperado:",data)
            else:
                ntimes=ntimes+1
                if(ntimes>threshold):
                    print("Fin calibración.")
                    remove("QRcalibracionTX.png")
                    print("Confirmación Repetida demasiadas veces. Terminando")
                    capture.release()
                    cv2.destroyAllWindows()
                    break

            
        else:
            if first:
                showQR(img,0,0,1)
                ntimes=ntimes+1
                time.sleep(0.5)
                if ntimes>threshold:
                    print("Receptor no inicia.")
                    remove("QRcalibracionTX.png")
                    capture.release()
                    cv2.destroyAllWindows()
                    break
            else:
                showQR(img,0,0,1)
                ntimes=ntimes+1
                if ntimes>threshold:
                    print("Lectura vacía demasiadas veces.")
                    remove("QRcalibracionTX.png")
                    capture.release()
                    cv2.destroyAllWindows()
                    break

    print("La version más grande aceptada es :", str(v-1))
    global maxversion
    maxversion=v-1
     

def sendTX(max_version, filename):
    if max_version>=3:
        estimated=0
        ntimes=0
        data_ant="No data before."
        threshold=100
        first=True
        #Generar el primer QR que es va a enviar.
        hash=md5(filename)
        print("Hash:",hash)
        size=sizeFile(filename)
        n_paq=math.ceil(size/getCapacity(max_version))
        generateQR(hash+str(len(filename))+filename+str(n_paq),3,"QRsendTX.png")
        #Tiempo en generar el QR.
        #generateQR(hash+str(len(filename))+filename+str(len(str(n_paq)))+str(n_paq),3,"QRsendTX.png")
        # Send the chunk to the client
        img=cv2.imread("QRsendTX.png")
        showQR(img,0,0,1)
        #Image capture starts.
        capture=cv2.VideoCapture(0)
        with open(filename, "rb") as file:
            # Read the file in chunks
            chunk = file.read(getCapacity(max_version))
            chunk64=base64. b64encode(chunk)
            if len(chunk64)>getCapacityMax(max_version):
                print("Error con el base 64 y los tamaños.")
            while chunk and capture.isOpened():
                ret, frame = capture. read()
                data=readQR(frame)
                if data!=None:
                    first=False
                    if(data!=data_ant):
                        ntimes=0
                        data_ant=data
                        if data.decode()==str(estimated):
                            #print("chunk:",estimated)
                            estimated=estimated+1
                            #Update data to send
                            generateQR(chunk64,max_version,"QRsendTX.png")
                            img=cv2.imread("QRsendTX.png")
                            showQR(img,0,0,1)
                            chunk = file.read(getCapacity(max_version))
                            chunk64=base64.b64encode(chunk)
                            if len(chunk64)>getCapacityMax(max_version):
                                print("Error con el base 64 y los tamaños.")

                        elif data=="Fin":
                            print("Fin TX.")
                            print(data)
                            capture.release()
                            cv2.destroyAllWindows()
                            break
                        else:
                            ntimes=ntimes+1
                            if(ntimes>threshold):
                                print("Fin calibración.")
                                print("Confirmación inesperada mayor que umbral de error. Terminando")
                                capture.release()
                                cv2.destroyAllWindows()
                                break

                            print("ERROR.QR no esperado:",data)
                    else:
                        ntimes=ntimes+1
                        showQR(img,0,0,1)
                        if(ntimes>threshold):
                            print("Fin calibración.")
                            remove("QRsendTX.png")
                            print("Confirmación Repetida demasiadas veces. Terminando")
                            capture.release()
                            cv2.destroyAllWindows()
                            break

                #Read None    
                else:
                    if first:
                        print("Esperando al RX. "+str(ntimes))
                        showQR(img,0,0,1)
                        ntimes=ntimes+1
                        time.sleep(0.5)
                        if ntimes>threshold:
                            print("Receptor no inicia.")
                            capture.release()
                            cv2.destroyAllWindows()
                            break
                    else:
                        showQR(img,0,0,1)
                        ntimes=ntimes+1
                        if ntimes>threshold:
                            print("Lectura vacía demasiadas veces.")
                            capture.release()
                            cv2.destroyAllWindows()
                            break
            remove("QRsendTX.png")                    
            print("Paquetes confirmados:",str(estimated))
            showQR(img,0,0,5000)
            capture.release()
            cv2.destroyAllWindows()
            return size
            
    else:
        print("La versión máxima utilizable es muy pequeña pruebe a lanzar de nuevo.")
   
def getCapacityMax(version):
    capacity=[17,32,53,78,106,134,154,192,230,271,321,367,425,458,520,586,644,718,792,858,929,1003,1091,1171,1273,1367,1465,1528,1628,1732,1840,1952,2068,2188,2303,2431,2563,2699,2809,2953]
    if version >0 and version <=40:
        return capacity[version-1]
    else:
        return -1
    
def getCapacity(version):
    capacityReal=[12,24,39,57,78,99,114,144,171,201,240,273,318,342,390,438,483,537,594,642,696,750,816,876,954,1023,1098,1146,1221,1299,1380,1464,1551,1641,1725,1821,1920,2022,2106,2214]
    if version >0 and version <=40:
        return capacityReal[version-1]
    else:
        return -1  
      
def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def selectFile():
    return askopenfilename(title="Seleccionar archivo")

def sizeFile(filename):
    return os.stat(filename).st_size

def readHeader(header):
    hash=header[0:32]
    name_size=header[32]
    name=header[33:33+int(name_size)]
    n_paq=header[33+int(name_size):]
    return [hash,name_size,name,n_paq]

if __name__ == "__main__":
    app = App()
    app.mainloop()
