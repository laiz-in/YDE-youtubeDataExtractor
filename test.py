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

#importing all the necessary libraries


app = Flask(__name__)
@app.route('/',methods=['GET'])
@cross_origin()
def mainpage():
    return render_template("index.html")

@app.route('/scrape', methods=['GET','POST'])
@cross_origin()
def index():
    if request.method == 'POST':
        try:

            youtuber_name = request.form['youtubername']
            youtuber = youtuber_name.lower()
            if (youtuber == "tulesko"):
                youtubeurl = "https://www.youtube.com/c/Telusko/videos"
            elif (youtuber == "krish naik"):
                youtubeurl = "https://www.youtube.com/user/krishnaik06/videos"
            elif (youtuber == "mysirg"):
                youtubeurl = "https://www.youtube.com/user/saurabhexponent1/videos"
            elif (youtuber == "hitesh choudhary"):
                youtubeurl = "https://www.youtube.com/c/HiteshChoudharydotcom/videos"
            else:
                k = ("type youtube channel name properly as we have added only 4 channels ")
                return None
            #inittializing the chrome
            driver = webdriver.Chrome('chromedriver.exe')
            driver.get(youtubeurl)
            #scrolling down by 4000px to fetch first 50 video details
            driver.execute_script("window.scrollBy(0,4000)", "")
            time.sleep(5)
            #scrapping the video titles by using selenium xpath method
            videos = driver.find_elements("xpath", '//*[@id="video-title"]')
            #scrapping the Published date
            publishdate = driver.find_elements("xpath", '//*[@id="metadata-line"]/span[2]')
            #scrapping the thumbnail URL
            thumb = driver.find_elements("xpath", '//*[@id="dismissible"]/ytd-thumbnail/a/yt-img-shadow/img')
            driver.execute_script("window.scrollBy(0,10000)", "")
            PublishedDate = []
            VideoTitle = []
            VideoLink = []
            Views = []
            comments = []
            #looping through titles ,publishedDates and thumbnail urls to store all 50 datas
            for i, k, m in zip(videos, publishdate, thumb):
                V = (i.get_attribute('href'))
                #avoiding scrapping out the datas for YouTube shorts
                if V[24:30] == "shorts":
                   continue
                #appending datas to the corresponding lists
                VideoLink.append(V)
                VideoTitle.append(i.get_attribute('text'))
                PublishedDate.append(k.text)
                #stopping the loop when the array reaches 50 videos
                if len(PublishedDate) == 50:
                    break
            #closing the chrome selenium driver
            driver.close()

            #scrapping the video lenghth and thumbnail url by pytube module, its possible even with selenium
            lenghth=[]
            thumbnails=[]
            try:
                for i in VideoLink:
                    insidevid = YouTube(i)
                    lenghth.append(int((insidevid.length)/60))
                    thumbnails.append(insidevid.thumbnail_url)
            except:
                print("error occured while executing pytube")

            #extracting the video ID from the video URLs
            videoIDs = []
            for i in VideoLink:
                videoIDs.append(i.split("=")[1])
            #scrapping the comments, total number of comments, total views using YouTube data api
            TotalViews=[]
            TotalComments=[]
            LikeCount=[]
            comments = []
            api_key = "AIzaSyAV8gm5shd19I14G6R0H86GKtCZvJW8naI"
            try:
                #looping through each videos
                for i in videoIDs:
                    resource = build('youtube', 'v3', developerKey=api_key)

                    #scrapping the comments,comments will be stored as list with commenter name
                    request = resource.commentThreads().list(
                        part="snippet",
                        videoId=i,
                        maxResults=20,
                        order="time")
                    response = request.execute()
                    items = response["items"][:100]
                    comm=[]
                    for item in items:
                        item_info = item["snippet"]
                        topLevelComment = item_info["topLevelComment"]
                        comment_info = topLevelComment["snippet"]
                        s = ("{0} : {1}".format(comment_info["authorDisplayName"], comment_info["textDisplay"]))
                        comm.append(s)
                    comments.append(comm)

                    #scrapping the video statistics such as total likes, total views, total number of comments
                    request = resource.videos().list(
                        part="statistics",
                        id=i)
                    response2 = request.execute()
                    k = (response2["items"])
                    commcount = k[0]
                    stat = (commcount['statistics'])
                    TotalComments.append(int(stat['commentCount']))
                    LikeCount.append(int(stat['likeCount']))
                    TotalViews.append(int(stat['viewCount']))
            except:
                print("error occured while scrapping comments and statistics")
            #converting the thumbnails into BASE64 format using base64 module
            thumb64=[]
            try:
                for i in thumbnails:
                    x= base64.b64encode(requests.get(i).content)
                    thumb64.append(x)
            except:
                print("something went wrong with converting thumbnail into base64 format")
            #creating the CSV file
            filenameCSV = youtuber + ".csv"
            datas = [VideoLink,VideoTitle,PublishedDate,lenghth,TotalViews,LikeCount,TotalComments,comments,thumbnails,thumb64]
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
            with open(filenameCSV, 'w', encoding='UTF8',newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerow(datas)
            #creating the xlsx file
            filenameEXCEL = youtuber + ".xlsx"
            writer = pd.ExcelWriter(filenameEXCEL, engine='xlsxwriter')
            writer.save()
            df = pd.read_excel(filenameEXCEL)
            df = pd.DataFrame({'VideoLinks': VideoLink,
                               'VideoTitles':VideoTitle,
                               'Published': PublishedDate,
                               'video lenghth': lenghth,
                               'ViewCount':TotalViews,
                               'TotalLikes': LikeCount,
                               'TotalComments':TotalComments,
                               'comments with author name':comments,
                               'ThumbnailLinks':thumbnails,
                               "ThumbnailsBASE64" : thumb64
                               })
            writer = pd.ExcelWriter(filenameEXCEL, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Sheet1', index=False)
            writer.save()
            # print("video links are = ", VideoLink)
            # print(len(VideoLink))
            # print("video titles are = ", VideoTitle)
            # print(len(VideoTitle))
            # print("publish date = ", PublishedDate)
            # print(len(PublishedDate))
            # print("comments = ", comments)
            # print("Video lenghth  =", lenghth)
            # print(len(lenghth))
            # print("total comments on the video = ", TotalComments)
            # print(len(TotalComments))
            # print("total likes of the video = ", LikeCount)
            # print(len(LikeCount))
            # print("total views = ", TotalViews)
            # print(len(TotalViews))
            # print("thumbnail URLs = ", thumbnails)
            # print(len(thumbnails))
            # # print("thumbnails in base64 = ", thumb64)
            # print(len(thumb64))
            datas = []
            dic = {'VideoLinks': VideoLink,
                   'VideoTitles': VideoTitle,
                   'Published': PublishedDate,
                   'video lenghth': lenghth,
                   'ViewCount': TotalViews,
                   'TotalLikes': LikeCount,
                   'TotalComments': TotalComments,
                   'comments with author name': comments,
                   'ThumbnailLinks': thumbnails,
                   }
            datas.append(dic)
            return render_template('results.html', datas=datas[0:(len(datas)-1)])
        except Exception as e:
            print((e))
            return "oops something went wrong!!!!"

    else:
        return render_template('index.html')

if __name__ == "__main__":
    #app.run(host='127.0.0.1', port=5001, debug=True)
	app.run(debug=True)



