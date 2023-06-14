from app import app
from flask import Flask, render_template, request, redirect, url_for
import requests
import pandas as pd
import json
import os
from bs4 import BeautifulSoup
from app.utils import get_element, selectors
from matplotlib import pyplot as plt
import numpy as np
@app.route("/")
def index():
    return render_template('main_page.html')


@app.route("/name",defaults={'name' :"Anonim"})
@app.route("/name/<name>")
def name(name):
    return f"Hello {name}"

@app.route("/o_autorze")
def author():
    return render_template('author.html')

@app.route("/ekstrakcja", methods=['POST','GET'])
def extraction():
    if request.method == 'POST':
        product_code = request.form.get('product_code')
        url = f"https://www.ceneo.pl/{product_code}#tab=reviews"
        all_opinions = []
        while(url):
            print(url)
            response = requests.get(url)
            page_dom = BeautifulSoup(response.text, "html.parser")
            opinions = page_dom.select("div.js_product-review")
            for opinion in opinions:
                single_opinion = {}
                for key, value in selectors.items():
                    single_opinion[key] = get_element(opinion, *value)
                all_opinions.append(single_opinion)
            try:    
                url = "https://www.ceneo.pl"+get_element(page_dom,"a.pagination__next","href")
            except TypeError:
                url = None
        if not os.path.exists("./app/data/opinions"):
            os.mkdir("./app/data/opinions")
        with open(f"./app/data/opinions/{product_code}.json", "w", encoding="UTF-8") as jf:
            json.dump(all_opinions, jf, indent=4, ensure_ascii=False)
        opinions = pd.read_json(json.dumps(all_opinions,ensure_ascii=False))
        opinions.score = opinions.score.map(lambda x: float(x.split("/")[0].replace(",",".")))
        stats = {
            "opinions_count": int(opinions.opinion_id_count()),
            "pros_count": int(opinions.pros.map(bool).sum()),
            "cons_count": int(opinions.cons.map(bool).sum()),
            "avg_score": opinions.score.mean().round(2)
        }
        score = opinions.score.value_counts().reindex(list(np.arange(0,5.5,0.5)), fill_value = 0)
        score.plot.bar(color="hotpink")
        plt.xticks(rotation=0)
        plt.title("Histogram ocen")
        plt.xlabel("Liczba gwiazdek")
        plt.ylabel("Liczba opinii")
        plt.ylim(0,max(score.values)+1.5)
        for index, value in enumerate(score):
            plt.text(index, value+0.5, str(value), ha="center")
        try:
            os.mkdir("./app/static/plots")
        except FileExistsError:
            pass
        plt.savefig(f"./app/static/plots/{product_code}_score.png")
        plt.close()
        recommendation = opinions["recommendation"].value_counts(dropna = False).reindex(["Nie polecam", "Polecam", np.nan])
        print(recommendation)
        recommendation.plot.pie(
            label="", 
            autopct="%1.1f%%",
            labels = ["Nie polecam", "Polecam", "Nie mam zdania"],
            colors = ["crimson", "forestgreen", "gray"]
        )
        plt.legend(bbox_to_anchor=(1.0,1.0))
        plt.savefig(f"./app/static/plots/{product_code}_recommendation.png")
        plt.close()
        stats['score'] = score.to_dict()
        stats['recommendation'] = recommendation.to_dict()
        try:
            os.mkdir("./app/static/stats")
        except FileExistsError:
            pass
        with open(f"./app/static/stats/{product_code}.json", "w", encoding="UTF-8") as jf:
            json.dump(stats, jf, indent=4,ensure_ascii=False)
        return redirect(url_for('product', product_code=product_code))
    return render_template('extract.html')   
        
            
            

@app.route("/lista_produktów")
def productList():
    return render_template('product_list.html')

@app.route("/product/<code>")
def product():
    opinions = pd.read_json(f"./app/data/opinions/{code}.json")
    return render_template('product.html', product_code = code, opinions = opinions.to_html(header = "true",table_id = "product_table",classes = "table"))

@app.route("/wykresy")
def charts():
    return render_template('charts.html')