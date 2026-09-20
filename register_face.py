import cv2
import os

name = input("Enter your name: ")
cam = cv2.VideoCapture(0)

print("Camera opening... position your face in center!")
print("Press SPACE to capture your photo!")

while True:
    ret, frame = cam.read()
    if not ret:
        continue
    
    # Show live window
    cv2.imshow("Position your face in center - Press SPACE to capture!", frame)
    
    key = cv2.waitKey(1)
    
    # Press SPACE to capture
    if key == ord(' '):
        if not os.path.exists("Known_faces"):
            os.makedirs("Known_faces")
        path = f"Known_faces/{name}.jpg"
        cv2.imwrite(path, frame)
        print(f"✅ Face saved as {path}")
        break
    
    # Press Q to quit
    if key == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()