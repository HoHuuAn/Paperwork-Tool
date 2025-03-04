import numpy as np
import cv2

def mapp(h):
    h = h.reshape((4,2))
    hnew = np.zeros((4,2), dtype = np.float32)

    add = h.sum(1)
    hnew[0] = h[np.argmin(add)]
    hnew[2] = h[np.argmax(add)]

    diff = np.diff(h, axis = 1)
    hnew[1] = h[np.argmin(diff)]
    hnew[3] = h[np.argmax(diff)]

    return hnew

def scan(url: str):
    image=cv2.imread(url)
    image=cv2.resize(image,(1300,800))
    orig=image.copy()

    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)  

    blurred=cv2.GaussianBlur(gray,(5,5),0) 

    edged=cv2.Canny(blurred,30,80) 


    contours,hierarchy=cv2.findContours(edged,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE) 
    contours=sorted(contours,key=cv2.contourArea,reverse=True)
    for c in contours:
        p=cv2.arcLength(c,True)
        approx=cv2.approxPolyDP(c,0.02*p,True)

        if len(approx)==4:
            target=approx
            break
    approx=mapp(target)

    pts=np.float32([[0,0],[800,0],[800,800],[0,800]]) 

    op=cv2.getPerspectiveTransform(approx,pts) 
    dst=cv2.warpPerspective(orig,op,(800,800))

    a4_dims = (2480, 3508) 

    pts_a4 = np.float32([[0, 0], [a4_dims[0], 0], [a4_dims[0], a4_dims[1]], [0, a4_dims[1]]]) 

    op_a4 = cv2.getPerspectiveTransform(approx, pts_a4)  
    dst_a4 = cv2.warpPerspective(orig, op_a4, a4_dims) 

    cv2.imwrite(url, dst_a4)