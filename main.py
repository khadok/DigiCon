import os
import sys
import logging
from PyQt4 import QtGui, QtCore
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import time
import requests
import json
import cv2 as cv
import numpy as np
from reportlab.pdfgen import canvas
import qdarkstyle

def setupLogging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    loggerHandler = logging.StreamHandler(sys.stdout)
    loggerHandler.setLevel(logging.DEBUG)
    loggerFormatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    loggerHandler.setFormatter(loggerFormatter)
    logger.addHandler(loggerHandler)

def SaveFigureAsImage(fileName,fig=None,**kwargs):
    fig_size = fig.get_size_inches()
    w,h = fig_size[0], fig_size[1]
    fig.patch.set_alpha(0)
    if kwargs.has_key('orig_size'): # Aspect ratio scaling if required
        w,h = kwargs['orig_size']
        w2,h2 = fig_size[0],fig_size[1]
        fig.set_size_inches([(w2/w)*w,(w2/w)*h])
        fig.set_dpi((w2/w)*fig.get_dpi())
    a=fig.gca()
    a.set_frame_on(False)
    a.set_xticks([]); a.set_yticks([])
    plt.axis('off')
    plt.xlim(0,h); plt.ylim(w,0)
    fig.savefig(fileName, transparent=True, bbox_inches='tight',pad_inches=0)

def SaveFigureAsImage(fileName,fig=None):
    fig_size = fig.get_size_inches()
    w,h = fig_size[0], fig_size[1]
    fig.patch.set_alpha(0)
    a=fig.gca()
    a.set_frame_on(False)
    a.set_xticks([]); a.set_yticks([])
    plt.axis('off')
    plt.xlim(0,h); plt.ylim(w,0)
    fig.savefig(fileName, transparent=True, bbox_inches='tight',pad_inches=0)

def azureCVDispProcessing(analysis, image_path):
    polygons = [(line["boundingBox"], line["text"]) for line in analysis["recognitionResult"]["lines"]] 
    img_path = str(image_path)
    print(img_path)
    img = cv.imread(img_path)
    height, width, channels = img.shape
    bg_img = img
    for polygon in polygons:
        vertices = [(polygon[0][i], polygon[0][i+1]) for i in range(0,len(polygon[0]),2)]
        cv.fillPoly(bg_img, pts=np.int32([vertices]), color=(0,255,0))
    cv.imwrite('./temp/bg_img.jpg',bg_img)
    c.drawImage('./temp/bg_img.jpg',0,0)    
    for polygon in polygons:
        vertices = [(polygon[0][i], polygon[0][i+1]) for i in range(0,len(polygon[0]),2)]
        text     = polygon[1]
        # print vertices
        min_x = min(vertices, key = lambda t: t[0])[0]
        min_y = min(vertices, key = lambda t: t[1])[1]
        max_x = max(vertices, key = lambda t: t[0])[0]
        max_y = max(vertices, key = lambda t: t[1])[1]
        # print min_x,min_y,max_x,max_y
        # cv.fillPoly(img, pts=np.int32([vertices]), color=(0,255,0))
        cv.rectangle(img,(min_x,min_y),(max_x,max_y),(0,255,0),cv.cv.CV_FILLED)
        cv.putText(img, text, vertices[0], cv.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 1 , cv.CV_AA)
        c.drawString(min_x,height-(min_y+max_y)/2,text)
    cv.imwrite( "./temp/azureCVDispProcessing.jpg", img)
    qimg = cv.cvtColor(img, cv.cv.CV_BGR2RGB)#for Qt display
    logging.debug('Image with ROI saved')
    c.save()
    return qimg

def azureDispProcessing(analysis, image_path):
    polygons = [(line["boundingBox"], line["text"]) for line in analysis["recognitionResult"]["lines"]] 
    plt.figure(figsize=(15,15))
    image  = mpimg.imread(image_path)
    ax     = plt.imshow(image)
    for polygon in polygons:
        vertices = [(polygon[0][i], polygon[0][i+1]) for i in range(0,len(polygon[0]),2)]
        text     = polygon[1]
        patch    = Polygon(vertices, closed=True,fill=True, linewidth=2, color='y')
        ax.axes.add_patch(patch)
        plt.text(vertices[0][0], vertices[0][1], text, fontsize=20, va="top")
    _ = plt.axis("off")
    plt.show(block=False)
    logging.debug('Image with ROI saved')

def imageAzureHandwriting(image_path):
    subscription_key = "00c800bde4fe46b7b36fc42aba617e6b"
    assert subscription_key
    vision_base_url = "https://westcentralus.api.cognitive.microsoft.com/vision/v1.0/"
    text_recognition_url = vision_base_url + "RecognizeText"

    # using image in disk
    image_data = open(image_path, "rb").read()
    headers    = {'Ocp-Apim-Subscription-Key': subscription_key, 
              "Content-Type": "application/octet-stream" }
    params   = {'handwriting' : True}
    response = requests.post(text_recognition_url, headers=headers, params=params, data=image_data)
    response.raise_for_status()
    
    operation_url = response.headers["Operation-Location"]
    analysis = {}
    while not "recognitionResult" in analysis:
        logging.info('Polling azure GET')
        response_final = requests.get(response.headers["Operation-Location"], headers=headers)
        analysis       = response_final.json()
        time.sleep(1)
    qimg = azureCVDispProcessing(analysis=analysis, image_path=image_path)
    return qimg, analysis

def imageDenoising(img):
    img= cv.cvtColor(img, cv.COLOR_RGB2GRAY)
    return img

def imageBinarization(img):
    # global thresholding
    ret1,th1 = cv.threshold(img,127,255,cv.THRESH_BINARY)
    # Otsu's thresholding
    ret2,th2 = cv.threshold(img,0,255,cv.THRESH_BINARY+cv.THRESH_OTSU)
    # Otsu's thresholding after Gaussian filtering
    blur = cv.GaussianBlur(img,(3,3),0)
    ret3,th3 = cv.threshold(blur,0,255,cv.THRESH_BINARY+cv.THRESH_OTSU)
    return th3

def imageLOTDetection():
    pass

def imageWordROIDetection():
    pass

def imageNNWordDetection():
    pass

def imageWordSpellcorrection():
    pass
def imageWordToList(analysis, binarisedImg):
    wordROIList = []
    polygons = [(line["boundingBox"], line["text"]) for line in analysis["recognitionResult"]["lines"]] 
    # img_path = str(image_path)
    # print(img_path)
    # img = cv.imread(img_path)
    height, width, channels = binarisedImg.shape
    print height, width, channels
    # c.drawImage('./temp/bg_img.jpg',0,0)    
    for polygon in polygons:
        vertices = [(polygon[0][i], polygon[0][i+1]) for i in range(0,len(polygon[0]),2)]
        text     = polygon[1]
        min_x = min(vertices, key = lambda t: t[0])[0]
        min_y = min(vertices, key = lambda t: t[1])[1]
        max_x = max(vertices, key = lambda t: t[0])[0]
        max_y = max(vertices, key = lambda t: t[1])[1]
        roi = binarisedImg[min_y:max_y,min_x:max_x]
        wordROIList.append(roi)
        # cv.imshow("dsdsd",roi )
        # cv.waitKey(0)
    return wordROIList
    # cv.imwrite( "./temp/azureCVDispProcessing.jpg", img)
    
class Window(QtGui.QMainWindow):
    image_path = ''
    imageSeq = []
    currentSeq = -1
    processingComplete = False

    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(50, 50, 1024, 768)
        self.setWindowTitle("DigiCon")

        self.lbl = QtGui.QLabel(self)
        self.setCentralWidget(self.lbl)
        
        self.lbl.progressBar = QtGui.QProgressBar(self)
        self.lbl.progressBar.setGeometry(QtCore.QRect(20, 20, 1024, 30))
        self.lbl.progressBar.setRange(0,1024)
        self.lbl.progressBar.setProperty("value", 1)
        self.lbl.progressBar.move(0,500)
        self.lbl.progressBar.setVisible(False)

        openFile = QtGui.QAction("&File", self)
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip("Open File")
        openFile.triggered.connect(self.file_open)

        self.statusBar()
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(openFile)

        

        self.home()

    def home(self):
        self.process_btn = QtGui.QPushButton("Process", self)
        self.process_btn.clicked.connect(lambda: self.processImage())
        self.process_btn.resize(100,100)
        self.process_btn.move(100,100)
        self.process_btn.setVisible(False)

        self.open_btn = QtGui.QPushButton("Open an image", self)
        self.open_btn.clicked.connect(lambda: self.file_open())
        self.open_btn.resize(100,100)
        self.open_btn.move(100,100)

        
        self.show()

    def file_open(self):
        self.image_path = QtGui.QFileDialog.getOpenFileName(self, 'Open File')
        logging.debug('Image path is' + self.image_path)

        self.open_btn.setVisible(False)
        self.lbl.progressBar.setVisible(True)
        self.process_btn.setVisible(True)

    def progressBarUpdate(self):
        self.lbl.progressBar.setValue(self.progressBarCurrent)
        self.progressBarCurrent += self.progressBarIncrement
        self.lbl.progressBar.repaint()

    def imageSeqHandler(self, _cvImg):
        if(len(_cvImg.shape) == 2):
            cvImg = cv.cvtColor(_cvImg, cv.COLOR_GRAY2RGB)
        else:
            cvImg = _cvImg
        height, width, channel = cvImg.shape
        bytesPerLine = channel*3 #Error prone in case of binarized images
        qImg = QtGui.QImage(cvImg, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
        # self.imageSeq.append(QtGui.QPixmap(qImg))
        self.imageSeq.append(cvImg)
    def processingStepsHandler(self, cvImg):
        self.imageSeqHandler(cvImg)
        self.progressBarUpdate()

    def processImage(self):
        self.progressBarIncrement = 1024/8
        self.progressBarCurrent = self.progressBarIncrement

        virginImg = cv.imread(str(self.image_path))
        self.processingStepsHandler(virginImg)
        denoisedImg = imageDenoising(virginImg)
        self.processingStepsHandler(denoisedImg)
        binarisedImg = imageBinarization(denoisedImg)
        self.processingStepsHandler(binarisedImg)
        LOTDetectedImg = imageLOTDetection()
        self.processingStepsHandler(binarisedImg)
        wordROIDetectedImg = imageWordROIDetection()
        self.processingStepsHandler(binarisedImg)
        NNWordDetectedImg = imageNNWordDetection()
        self.processingStepsHandler(binarisedImg)
        wordSpellcorrectedImg = imageWordSpellcorrection()
        self.processingStepsHandler(binarisedImg)
        azuredImg, azureAnalysis = imageAzureHandwriting(self.image_path)
        self.processingStepsHandler(azuredImg)

        wordROIList = imageWordToList(azureAnalysis, virginImg)
        self.processingComplete = True
        self.lbl.setPixmap(QtGui.QPixmap("./test.jpg"))
        self.adjustSize()

        self.process_btn.setVisible(False)
        self.lbl.progressBar.setVisible(False)

    def dispalyHandler(self):
        print("display handler called")
        cv.imwrite("./temp/res.jpg",self.imageSeq[self.currentSeq])
        self.lbl.setPixmap(QtGui.QPixmap("./temp/res.jpg"))
        self.lbl.repaint()
        self.adjustSize()
    
    def leftKeyHandler(self):
        if(self.processingComplete == False):
            return
        if(self.currentSeq == 0):
            return
        self.currentSeq -= 1
        self.dispalyHandler()

    def rightKeyHandler(self):
        if(self.processingComplete == False):
            return
        if(self.currentSeq == len(self.imageSeq)-1):
            return
        self.currentSeq += 1
        self.dispalyHandler()
        
    def keyPressEvent(self, event):
        print("keyPressEvent happened",self.currentSeq, len(self.imageSeq))
        if event.key() == QtCore.Qt.Key_P:
            logging.info("Left key pressed")
            self.leftKeyHandler()
        elif event.key() == QtCore.Qt.Key_N:
            logging.info("Right key pressed")
            self.rightKeyHandler()
        event.accept()

def run():
    setupLogging()
    app = QtGui.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt())
    GUI = Window()
    sys.exit(app.exec_())

c = canvas.Canvas("./temp/test.pdf")
run()