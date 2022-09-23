@app.route('/scrap',methods=['POST','GET']) # route to show the review comments in a web UI
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            url = request.form['scrap'].replace(" ", "")
            print(url)
            video_url = VideoUrl.Video_page(url)
            all_video_link_of_channel = video_url['video_url']