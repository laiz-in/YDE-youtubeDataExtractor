from flask import Flask, render_template
from flask import request
from flask_cors import CORS,cross_origin
import requests
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import base64
import csv
from flask import Flask, current_app
from pytube import YouTube
from googleapiclient.discovery import build
import pymongo
import mysql.connector as conn


app = Flask(__name__)
@app.route('/',methods=['GET'])
@cross_origin()
def mainpage():
    return render_template('index.html')

@app.route('/scrape', methods=['GET','POST'])
@cross_origin()
def index():
    if request.method == 'POST':
        search = request.form['youtubername']
        youtuber_name = request.form['youtubername']
        youtuber = youtuber_name.lower()
        youtubersql= youtuber.replace(" ","")
        if (youtuber == "tulesko"):
            youtubeurl = "https://www.youtube.com/c/Telusko/videos"
        elif (youtuber == "krish naik"):
            youtubeurl = "https://www.youtube.com/user/krishnaik06/videos"
        elif (youtuber == "mysirg"):
            youtubeurl = "https://www.youtube.com/user/saurabhexponent1/videos"
        elif (youtuber == "hitesh choudhary"):
            youtubeurl = "https://www.youtube.com/c/HiteshChoudharydotcom/videos"
        else:
            p = "We have added only 4 youtubers , please check your input!"
            return render_template('errormsg.html',pk=p)
        try:
            driver = webdriver.Chrome('chromedriver.exe')
            driver.get(youtubeurl)
            # scrolling down by 4000px to fetch first 50 video details
            driver.execute_script("window.scrollBy(0,4000)", "")
            time.sleep(5)
            # scrapping the video titles by using selenium xpath method
            videos = driver.find_elements("xpath", '//*[@id="video-title"]')
            # scrapping the Published date
            publishdate = driver.find_elements("xpath", '//*[@id="metadata-line"]/span[2]')
            # scrapping the thumbnail URL
            thumb = driver.find_elements("xpath", '//*[@id="dismissible"]/ytd-thumbnail/a/yt-img-shadow/img')
            driver.execute_script("window.scrollBy(0,10000)", "")
            PublishedDate = []
            VideoTitle = []
            VideoLink = []
            Views = []
            comments = []
            # looping through titles ,publishedDates and thumbnail urls to store all 50 datas
            for i, k, m in zip(videos, publishdate, thumb):
                V = (i.get_attribute('href'))
                # avoiding scrapping out the datas for YouTube shorts
                if V[24:30] == "shorts":
                    continue
                # appending datas to the corresponding lists
                VideoLink.append(V)
                VideoTitle.append(i.get_attribute('text'))
                PublishedDate.append(k.text)
                # stopping the loop when the array reaches 50 videos
                if len(PublishedDate) == 50:
                    break
            # closing the chrome selenium driver
            driver.close()
        except Exception as e:
            p= "error happend while fetching links,titles and publish dates , error: " + e
            return render_template('errormsg.html',pk=p)

        # scrapping the video lenghth and thumbnail url by pytube module, its possible even with selenium
        lenghth = []
        thumbnails = []
        for i in VideoLink:
            insidevid = YouTube(i)
            lenghth.append(int((insidevid.length) / 60))
            thumbnails.append(insidevid.thumbnail_url)
        videoIDs = []
        for i in VideoLink:
            videoIDs.append(i.split("=")[1])
        # scrapping the comments, total number of comments, total views using YouTube data api
        TotalViews = []
        TotalComments = []
        LikeCount = []
        comments = []
        api_key = "AIzaSyAV8gm5shd19I14G6R0H86GKtCZvJW8naI"
        try:
            # looping through each videos
            for i in videoIDs:
                resource = build('youtube', 'v3', developerKey=api_key)
                request2 = resource.commentThreads().list(
                    part="snippet",
                    videoId=i,
                    maxResults=100,
                    order="time")
                response = request2.execute()
                items = response["items"][:100]
                comm = []
                for item in items:
                    item_info = item["snippet"]
                    topLevelComment = item_info["topLevelComment"]
                    comment_info = topLevelComment["snippet"]
                    s = ("{0} : {1}".format(comment_info["authorDisplayName"], comment_info["textDisplay"]))
                    comm.append(s)
                comments.append(comm)
                request2 = resource.videos().list(
                    part="statistics",
                    id=i)
                response2 = request2.execute()
                k = (response2["items"])
                commcount = k[0]
                stat = (commcount['statistics'])
                TotalComments.append(int(stat['commentCount']))
                LikeCount.append(int(stat['likeCount']))
                TotalViews.append(int(stat['viewCount']))
        except:
            p= "error occured while scrapping comments and statistics"
            return render_template('errormsg.html', pk=p)
        # converting the thumbnails into BASE64 format using base64 module
        thumb64 = []
        try:
            for i in thumbnails:
                x = base64.b64encode(requests.get(i).content)
                thumb64.append(x)
        except:
            p="something went wrong with converting thumbnail into base64 format"
            return render_template('errormsg.html',pk=p)

        #creating mongodb connection
        commentdict={"Comments": comments}
        thumb64dict = {"thumbnailsInBase64" : thumb64}
        client = pymongo.MongoClient("mongodb+srv://laizinv:laizin2107@cluster0.j7mdzpr.mongodb.net/?retryWrites=true&w=majority")
        dbname = youtuber + "_database"
        nm = dbname.replace(" ","")
        mydb = client[nm]
        mycol = mydb["ThumbnailsInBase64"]
        mycol2 = mydb["CommentsWithCommenter"]
        mycol.insert_one(thumb64dict)
        mycol2.insert_one(commentdict)

        #creating mysql connection
        # mydb = conn.connect(
        #     host="localhost",
        #     user="root",
        #     password="****"
        #
        # )
        # mycursor = mydb.cursor()
        # databasename = youtubersql
        # tablename = databasename + "_database"
        # cmline1 = "CREATE DATABASE {}".format(databasename)
        # cmline2 = ("""CREATE TABLE {}.{}(
        #            VideoLink VARCHAR(100),
        #            Videotitle VARCHAR(100),
        #            PublishedDate VARCHAR(100),
        #            VideoLenghth VARCHAR(200),
        #            LikeCount VARCHAR(10),
        #            ViewCount VARCHAR(100),
        #            Totalcomments VARCHAR(100)
        #           )
        #           """.format(databasename, tablename))
        # mycursor.execute(cmline1)
        # mycursor.execute(cmline2)

        # for i, j, k, l, m, n,o in zip(VideoLinkSQL,VideotitleSQL,PublishSQL,lenghthSQL, LikeSQL, ViewSQL, CommentsCountSQL):
        #     q = "INSERT INTO %s.%s VALUES (dbname,tablename'%s','%s','%s','%s','%s','%s','%s')" % (i, j, k, l, m, n,o)
        #     mycursor.execute(q)
        # mydb.commit()
        # mydb.close()
        # creating the CSV file
        filenameCSV = youtuber + ".csv"
        datas = [VideoLink, VideoTitle, PublishedDate, lenghth, TotalViews, LikeCount, TotalComments, comments,
                 thumbnails, thumb64]
        header = ["VideoLinks",
                  "VideoTitles",
                  "PublishedDate",
                  "VideoLenghth",
                  "TotalVideoViews",
                  "TotalLikes",
                  "TotalComments",
                  "comments with author name",
                  "ThumbnailLinks",
                  "ThumbnailsBASE64"]
        with open(filenameCSV, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow(datas)
        # creating the xlsx file
        filenameEXCEL = youtuber + ".xlsx"
        writer = pd.ExcelWriter(filenameEXCEL, engine='xlsxwriter')
        writer.save()
        df = pd.read_excel(filenameEXCEL)
        df = pd.DataFrame({'VideoLinks': VideoLink,
                           'VideoTitles': VideoTitle,
                           'Published': PublishedDate,
                           'video lenghth': lenghth,
                           'ViewCount': TotalViews,
                           'TotalLikes': LikeCount,
                           'TotalComments': TotalComments,
                           'comments with author name': comments,
                           'ThumbnailLinks': thumbnails,
                           "ThumbnailsBASE64": thumb64
                           })
        writer = pd.ExcelWriter(filenameEXCEL, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1', index=False)
        writer.save()
        videolink= VideoLink
        videotitle= VideoTitle
        videolenghth=lenghth
        published = PublishedDate
        likecount= LikeCount
        viewcount= TotalViews
        totalcomments= TotalComments






        return render_template('results.html',youtubername= youtuber,videolink=videolink, videotitle=videotitle,published =published,videolenghth=videolenghth ,likecount=likecount,viewcount=viewcount,totalcomments=totalcomments)



if __name__ == "__main__":
    #app.run(host='127.0.0.1', port=5001, debug=True)
	app.run(debug=True)



