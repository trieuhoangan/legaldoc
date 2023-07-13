import math 
import os
import sys
import pandas as pd
import numpy as np
from rank_bm25 import BM25Okapi
import traceback
import json

import transformers
from transformers import (
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    EvalPrediction,
    HfArgumentParser,
    PretrainedConfig,
    Trainer,
    TrainingArguments,
    default_data_collator,
    set_seed,
)
from datasets import load_dataset
from transformers.trainer_utils import get_last_checkpoint
from transformers.utils import check_min_version
from transformers.utils.versions import require_version

def get_article(line):
    line = line.lower()
    article_num_text = line.split(".")[0]
    article_num_text = article_num_text.replace("điều","")
    article_num = article_num_text.strip()
    try:
        article_num = int(article_num)
        return article_num
    except:
        return -1

def load_law(file_law,law_name,result):
    with open(file_law,'r',encoding='utf-8') as f:
        lines = f.readlines()

    chapter = ""
    article=""
    content=[]
    in_chapter = 0
    in_article = 0
    law_title = lines[0]
    for line in lines:
        line = line.replace("\n","")
        line = (" ").join(line.split())
        if line!=" ":
            if "Chương" == line[:6]:
                chapter=line
                in_chapter=1
                in_article=0
                continue
            elif "Điều"== line[:4]:
                if get_article(line) >0:
                    if in_article==1:
                        key="{}-{}".format(law_name,article)
                        value="\n".join(content)
                        result[key]=value
                    article = get_article(line)
                    in_article=1
                    content=[law_title+line]
                else:
                    if in_article==1 and in_chapter==1:
                        content.append(line)
            else:
                if in_article==1 and in_chapter==1:
                    content.append(line)
    # print(result[list(result.keys())[0]])
    return result

def load_all_laws():
    # list_file = os.listdir("statue_laws")
    # file_list = [os.path.join("statue_laws",filename) for filename in list_file]
    # print(file_list)
    
    laws ={}
    file_list = ["statue_laws/law{}.txt".format(i) for i in range(17)]
    for i in range(len(file_list)):
        laws = load_law(file_list[i],i+1,laws)
    return laws

def load_csv(filename):
    df = pd.read_csv(filename,header=0,names=['STT','format','law','art','art_cont','quest','anws','A','B','C','D','note','comment'],usecols=['format','law','art','quest','anws','A','B','C','D'])
    data = df.values.tolist()
    clean_data = []
    for row in data:
        if isinstance(row[0], str)==True:
            
            clean_data.append(row)
            
            
    # print(clean_data)
    return clean_data

def compare_res(pred,Y,laws):
    true=0
    all=0
    for index, instance in enumerate(pred):
        y = Y[index][0]
        if y==instance and len(Y[index]) ==1:
            true+=1
        # else:
        #     print(instance)
        #     print(laws[instance])
        all+=1
    print(true/all)

def collect_quest_and_law(law,art,TF_Y):
    current_Y = []
    art = str(art)
    if "Điều" in art :
        art = art.split(" ")[1]
    for part in str(art).split(','):
        current_Y.append("{}-{}".format(law.split(".")[0],part.strip()))
    TF_Y.append(current_Y)
    
    return TF_Y

def create_corpus_from_dict(laws):
    corpus = []
    for key in laws:
        sents = []
        split_by_dot=laws[key].split("\n")
        # for dot_sent in split_by_dot:
        #     sents+=dot_sent.split(";")
        corpus+= split_by_dot
    tokienized_corpus = [sent.split(" ") for sent in corpus]
    return tokienized_corpus

def find_max_pred(pred_dict):
    
    max_key = ""
    max_num = 0
    # print(len(list(result_list.keys())))
    # print(pred_dict)
    for key in pred_dict:
        if pred_dict[key] > max_num:
            max_num = pred_dict[key]
            max_key = key
    return max_key

def get_pred_from_seperated_laws(quest,corpus,bm25,laws):
    ranked_sents = bm25.get_top_n(quest, corpus, n=15)
    # print(ranked_sents)
    result_list={}
    for sent in ranked_sents:
        real_sent = " ".join(sent)
        for key in laws:
            if real_sent in laws[key]:
                if key not in result_list:
                    num = 1
                else: 
                    num = result_list[key] + 1
                result_list[key] = num
    
    max_key = ""
    max_num = 0
    # print(len(list(result_list.keys())))
    # print(result_list)
    for key in result_list:
        if result_list[key] > max_num:
            max_num = result_list[key]
            max_key = key
    return max_key

def get_pred_from_laws(quest,bm25,laws_list):
    tokenized_quest = quest.split(" ")
    quest_score = bm25.get_scores(tokenized_quest)
    pos = np.argmax(quest_score)
    return laws_list[pos]

def load_data_from_json(filename):
    with open(filename,'r',encoding='utf-8') as f:
        data = json.load(f)
    # print(data)

    return data

def load_quest_from_json(filename,laws):
    data = load_data_from_json(filename)
    quests = []
    for row in data:
        instance = {}
        instance["id"] = row["quest_id"]
        instance["type"] = row["question_type"]
        instance["quest"] = row["text"]
        articles=[]
        if "relevant_articles" in row:
            for article in row["relevant_articles"]:
                art = article["article_id"].lower()
                law = article["law_id"].lower()
                law_id = get_law_id(law)
                # articles.append("{}-{}".format(law_id,art))
                key = "{}-{}".format(law_id,art)
                text = laws[key]
                articles.append(key,text)
            instance["articles"]=articles
        if "answer" in row:
            answer = row["answer"]
            instance["answer"]=answer
        if "choices" in row:
            instance["A"] = row["choices"]["A"]
            instance["B"] = row["choices"]["B"]
            instance["C"] = row["choices"]["C"]
            instance["D"] = row["choices"]["D"]
        quests.append(instance)
    return quests

def run():
    laws = load_all_laws()
    tokenized_laws = []
    laws_list = list(laws.keys())
    ########## corpus with original laws
    for key in laws:
        tokenized_laws.append(laws[key].split(" "))
    ########## corpus with tokenized laws
    # tokenized_laws = create_corpus_from_dict(laws)
    bm25 = BM25Okapi(tokenized_laws)


    list_file = os.listdir("data")
    file_list = [os.path.join("data",filename) for filename in list_file]
    for data_file in file_list:
        print(data_file)
        # data_file = "data/Chau.csv"
        try:
            data = load_csv(data_file)
            
            TF_Y = []
            TF_quest = []

            TN_quest = []
            TN_Y = []

            for row in data:
                art=row[2]
                if isinstance(row[3], str)==True:
                    if isinstance(row[2], float)==True:
                        if math.isnan(row[2])==True:
                            continue
                        else:
                            art=int(row[2])
                    if row[0]!="Trắc nghiệm":
                        TF_Y = collect_quest_and_law(row[1],art,TF_Y)
                        TF_quest.append(row[3])
                    else:
                        TN_Y = collect_quest_and_law(row[1],art,TN_Y)
                        TN_quest.append((row[3],row[5],row[6],row[7],row[8]))
            # print(laws)
            TF_pred_law = []
            TN_pred_law = []
            for quest in TF_quest:
                pred = get_pred_from_laws(quest,bm25,laws_list)
                # pred = get_pred_from_seperated_laws(quest,tokenized_laws,bm25,laws)
                TF_pred_law.append(pred)
            for quest in TN_quest:
                real_quest = quest[0]
                cur_res = {}
                for i in range(1,5):
                    ans = quest[i]
                    combination = "{}\n{}".format(real_quest,ans)
                    pred = get_pred_from_laws(combination,bm25,laws_list)
                    # pred = get_pred_from_seperated_laws(quest,tokenized_laws,bm25,laws)
                    if pred not in cur_res:
                        cur_res[pred] = 1
                    else:
                        cur_res[pred] = cur_res[pred] +1
                
                
                pred = find_max_pred(cur_res)
                TN_pred_law.append(pred)

            # print(TF_pred_law)
            # print(TF_Y)
            pred = TF_pred_law+TN_pred_law
            Y = TF_Y + TN_Y 
            compare_res(pred,Y,laws)
        except:
            traceback.print_exception(*sys.exc_info())
            continue

def get_law_id(law_name):
    laws_name=[
        "HIẾN PHÁP",
        "BỘ LUẬT DÂN SỰ",
        "LUẬT Trọng tài thương mại",
        "LUẬT BẢO VỆ MÔI TRƯỜNG",
        "LUẬT Hôn nhân và gia đình",
        "LUẬT AN NINH MẠNG",
        "LUẬT TỐ TỤNG HÀNH CHÍNH",
        "LUẬT Viên chức",
        "LUẬT GIÁO DỤC",
        "Luật Phòng, chống ma túy",
        "LUẬT CƯ TRÚ",
        "LUẬT THANH NIÊN",
        "LUẬT CHĂN NUÔI",
        "LUẬT TRỒNG TRỌT",
        "LUẬT ĐIỆN ẢNH",
        "LUẬT DU LỊCH",
        "LUẬT TIẾP CẬN THÔNG TIN"
    ]
    normed_laws_name = [name.lower() for name in laws_name]
    # print(normed_laws_name)
    id = normed_laws_name.index(law_name) +1
    return id

def run_json_task1():
    laws = load_all_laws()
    tokenized_laws = []
    laws_list = list(laws.keys())
    ########## corpus with original laws
    for key in laws:
        tokenized_laws.append(laws[key].split(" "))
    ########## corpus with tokenized laws
    # tokenized_laws = create_corpus_from_dict(laws)
    bm25 = BM25Okapi(tokenized_laws)
    data = load_data_from_json("train_data/public_test_GOLD.json")
    
    
    TF_Y = []
    TF_quest = []
    TN_quest = []
    TN_Y = []
    for row in data:
        type = row["question_type"]
        Ys = []
        for article in row["relevant_articles"]:

            art = article["article_id"]
            law = article["law_id"].lower()
            law_id = get_law_id(law)
            Ys.append("{}-{}".format(law_id,art))
        if type!="Trắc nghiệm":
            TF_Y.append(Ys)
            TF_quest.append(row["text"])
        else:
            TN_Y.append(Ys)
            TN_quest.append((row["text"],row["choices"]["A"],row["choices"]["B"],row["choices"]["C"],row["choices"]["D"]))
    TF_pred_law = []
    TN_pred_law = []
    for quest in TF_quest:
        pred = get_pred_from_laws(quest,bm25,laws_list)
        # pred = get_pred_from_seperated_laws(quest,tokenized_laws,bm25,laws)
        TF_pred_law.append(pred)
    for quest in TN_quest:
        real_quest = quest[0]
        cur_res = {}
        for i in range(1,5):
            ans = quest[i]
            combination = "{}\n{}".format(real_quest,ans)
            pred = get_pred_from_laws(combination,bm25,laws_list)
            # pred = get_pred_from_seperated_laws(quest,tokenized_laws,bm25,laws)
            if pred not in cur_res:
                cur_res[pred] = 1
            else:
                cur_res[pred] = cur_res[pred] +1
        
        
        pred = find_max_pred(cur_res)
        TN_pred_law.append(pred)

    # print(TF_pred_law)
    # print(TF_Y)
    pred = TF_pred_law+TN_pred_law
    Y = TF_Y + TN_Y 
    compare_res(pred,Y,laws)

def using_bert_model():
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    # model_config = "thaingo/vietAI-vit5-base-law"
    # model_config = "t5-small"
    model_config = "vinai/phobert-base-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_config)
    model = AutoModelForSequenceClassification.from_pretrained(model_config)
    input_ids = tokenizer(    "Studies have been shown that owning a dog is good for you", return_tensors="pt").input_ids  # Batch size 1
    outputs = model(input_ids=input_ids)
    last_hidden_states = outputs.last_hidden_state

def train():
    # model_config = "thaingo/vietAI-vit5-base-law"
    # model_config = "t5-small"
    model_config = "vinai/phobert-base-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_config)
    model = AutoModelForSequenceClassification.from_pretrained(model_config)
    laws = load_all_laws()
    quests = load_quest_from_json("train_data/train.json",laws)
    data = load_dataset(quests)
    return None



if __name__=="__main__":
    # load_csv("An.csv")
    # run()
    # run_json_task1()
    train()