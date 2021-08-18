import streamlit as st
import time
import numpy as np
from io import BytesIO
from PIL import Image
import os
import selenium
from selenium import webdriver
import boto3
import matplotlib.pyplot as plt
from rpa import *

##################### aws keys
Access_Key_ID='AKIA4RDZJU3SBN7UTW3Y'
Secret_Access_Key='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'
####################

# validation function
def validate(pan_dict,adhar_dict):
    common_feilds=list(set.intersection(set(adhar_dict.keys()),set(pan_dict.keys())))
    validate_dict={}
    for entry in common_feilds:
        if pan_dict[entry]==adhar_dict[entry]:
            validate_dict[entry]=True
        else:
            validate_dict[entry]=False
    return validate_dict

# adhar and pan file upload
#st.title('Adhar')
file1 = st.file_uploader('Upload An adhar Image')
#st.title('Pan')
file2 = st.file_uploader('Upload An pan Image')
# operate on images obtained from file
if file1 and file2:
    # preprocess images
    img1 = Image.open(file1)
    resized_image1 = img1.resize((678,381))
    resized_image1.save("test1.jpg")
    st.image(resized_image1)

    img2 = Image.open(file2)
    resized_image2 = img2.resize((995,638))
    resized_image2.save("test2.jpg")
    st.image(resized_image2)
    
    # upload files on aws
    aws_call(Access_Key_ID,Secret_Access_Key,'test1.jpg',name='test_img.jpg')
    aws_call(Access_Key_ID,Secret_Access_Key,'test2.jpg',name='test_img2.jpg')
    
    time.sleep(6)
    
    # get recent result from mongo db
    item=get_mongo()

    # show and validate
   
    for i in item:
        st.json(i)
        st.title('validation')
    # form validation  
        st.write(validate(i['adhar'],i['pan']))

    # form fill   

    form_fill()

