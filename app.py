from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
import logging
from pymongo import MongoClient

logging.basicConfig(filename="scrapper.log", level=logging.INFO)

app = Flask(__name__)

@app.route("/", methods=['GET'])
def homepage():
    return render_template("index.html")

@app.route("/review", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ", "")
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            uClient = requests.get('http://splash:8050/render.html', params={'url': flipkart_url, 'wait': 5})
            flipkartPage = uClient.text
            flipkart_html = bs(flipkartPage, "html.parser")
            bigboxes = flipkart_html.findAll("div", {"class": "cPHDOP col-12-12"})
            del bigboxes[0:3]
            box = bigboxes[0]
            productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
            prodRes = requests.get('http://splash:8050/render.html', params={'url': productLink, 'wait': 5})
            prod_html = bs(prodRes.text, "html.parser")
            commentboxes = prod_html.find_all("div", {"class": "RcXBOT"})

            reviews = []
            for commentbox in commentboxes:
                try:
                    name = commentbox.div.div.find_all("p", {"class": "_2NsDsF AwS1CA"})[0].text
                except:
                    name = 'No Name'

                try:
                    rating = commentbox.div.div.div.div.text
                except:
                    rating = 'No Rating'

                try:
                    commentHead = commentbox.div.div.div.p.text
                except:
                    commentHead = 'No Comment Heading'

                try:
                    comtag = commentbox.div.div.find_all('div', {'class': ''})
                    custComment = comtag[0].div.text
                except Exception as e:
                    custComment = 'No Comment'
                    logging.info(e)

                mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                          "Comment": custComment}
                reviews.append(mydict)

            logging.info("log my final result {}".format(reviews))

            mongo_uri = "mongodb+srv://test:test1234567890@cluster0.fj7tf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
            client = MongoClient(mongo_uri)
            db = client['review_scrap'] 
            review_col = db['review_scrap_data'] 
            review_col.insert_many(reviews)


            return render_template('result.html', reviews=reviews[0:(len(reviews)-1)])
        except Exception as e:
            logging.error(f"Error occurred: {e}")  # Log the exact error
            return f'Something is wrong: {e}'  # Return the error message for debugging
    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
