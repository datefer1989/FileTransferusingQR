# FileTransferusingQR
Sistema de transferencia de archivos usando códigos QR en Python

Instalación de las librerías no incluidas por defecto:
pip3 install opencv-python
pip install pyzbar
(Según mi instalación de Python, y sin añadir ni quitar nada de las cosas predefinidas, sólo hay que añadir estas dos.)

Se recomienda calibrar antes de enviar, sino se coge una versión qr muy pequeña para el envío.
Una vez realizada la calibración se pueden enviar tantos archivos como se desee, el único requisito es que el nombre del archivo sea inferior a 10 incluyendo la extensión.
Para maximizar el rendimiento he realizado una calibración previa en mi pantalla dónde maximizo el tamaño pero consiguiendo que no se omita nada del qr. Sin esta 
maximización el programa podría funcionar pero muy pobremente. Cualquier duda al respecto ruego se me consulte.
