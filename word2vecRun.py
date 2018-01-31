from gensim.models import word2vec
model = word2vec.Word2Vec.load("./model/digitaltimes.model")
print("Word2Vec 모델 사용해보기")

while(True):
    word = input("단어를 입력하세요 :")
    result = model.wv.most_similar(positive=[word])
    print(result)
