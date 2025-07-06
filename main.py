import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# FastAPIアプリの初期化
app = FastAPI()

# データベースファイル名
DB_FILE = "wnjpn.db"

# 日本語の類義語を検索する関数
def find_synonyms(word_text):
    # データベースに接続
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()

    # 1. 入力された単語から、対応するsynset (同義語グループのID) を探す
    cur.execute("""
        SELECT synset FROM sense
        WHERE wordid = (SELECT wordid FROM word WHERE lemma = ?)
    """, (word_text,))
    
    synset_results = cur.fetchall()
    if not synset_results:
        return [] # 単語が見つからない場合

    # 2. 見つかったsynsetに属するすべての単語を取得する
    synonyms = set()
    for synset_id_tuple in synset_results:
        synset_id = synset_id_tuple[0]
        cur.execute("""
            SELECT w.lemma FROM sense s
            JOIN word w ON s.wordid = w.wordid
            WHERE s.synset = ?
        """, (synset_id,))
        
        words_in_synset = cur.fetchall()
        for word_tuple in words_in_synset:
            synonyms.add(word_tuple[0])

    con.close()
    
    # 元の単語は除外して返す
    synonyms.discard(word_text)
    return sorted(list(synonyms))


# APIのエンドポイント (URLのパス) を定義
@app.get("/synonyms/{word}")
def get_synonyms(word: str):
    # 日本語の文字化けを防ぐための設定
    if not word.isascii():
        word = word.encode('utf-8').decode('utf-8')

    synonyms_list = find_synonyms(word)
    
    if not synonyms_list:
        raise HTTPException(status_code=404, detail="単語が見つからないか、類義語がありません。")

    # 結果をJSONで返す
    return JSONResponse(
        content={"word": word, "synonyms": synonyms_list},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

# ルートURLに簡単な説明を表示
@app.get("/")
def read_root():
    return {"message": "日本語WordNet類義語API。/synonyms/{単語} の形式でアクセスしてください。例: /synonyms/猫"}
