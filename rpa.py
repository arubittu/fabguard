import selenium
from selenium import webdriver
import boto3
import pymongo
from pymongo import MongoClient
import time
#from boto3.s3.key import Key
################ aws access keys
Access_Key_ID='fill your keys'
Secret_Access_Key='fill your keys'
################ 
# uploading image on aws s3 after getting it from user
def aws_call(Access_Key_ID,Secret_Access_Key,path,name='test_img.jpg'):
    s3 = boto3.client(
        's3',
        aws_access_key_id=Access_Key_ID,
        aws_secret_access_key=Secret_Access_Key
        )
        #aws_session_token=SESSION_TOKEN
    rs=boto3.resource('s3')
    response = s3.list_buckets()
    s3.upload_file(path, 'fabgard', name)
    print('Existing buckets:')
    for bucket in response['Buckets']:
        print(f'  {bucket["Name"]}')
    

###################################
    #getting mongodb details of the user
def get_mongo():
    client = MongoClient("fill your keys")
    myDB = client['fabguard']
    mycollection = myDB.user
    item=myDB.user.find().sort('_id',-1).limit(1)
    client.close()
    return item

##################################
# runing selenium code for the above user details aqcuired from mongodb
def form_fill():
    item=get_mongo()
    item=[i for i in item]
    print(item)
    option=webdriver.ChromeOptions()
    option.add_argument("-incognito")
    driver=webdriver.Chrome(executable_path="D:\chromedriver_win32\chromedriver.exe",options=option)
    driver.maximize_window()
    driver.implicitly_wait(10)
    driver.get('https://docs.google.com/forms/d/e/1FAIpQLSdHX92AEkwRVkhF2j-jkNJR2gvJ6Ii2JFz1J4dBQp_rl1pHcw/viewform')
    t=driver.find_elements_by_class_name('quantumWizTextinputPaperinputInput.exportInput')
    submit=driver.find_element_by_class_name('appsMaterialWizButtonPaperbuttonLabel')
    t[0].send_keys(item[0]['adhar']['name'][0])
    time.sleep(0.5)
    t[1].send_keys(item[0]['adhar']['name'][1])
    time.sleep(0.5)
    t[2].send_keys(''.join(['2','10',item[0]['adhar']['dob'][0]]))
    time.sleep(0.5)
    t[3].send_keys(''.join(item[0]['adhar']['adhar_num']))
    
    #driver.find_element_by_name('btnK').submit()
    time.sleep(1)
    submit.click()
    time.sleep(2)
    driver.close()
    return 
    
if __name__=='__main__':
    form_fill()
