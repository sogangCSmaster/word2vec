"""
2017/12/06 Tue
0.개발환경
  - 파이썬 버전 : Python3.6.3
  - 필요 패키지 : beautifulsoup4(4.6.0), lxml(4.1.1), urllib3(1.22), requests(2.18.4)
    * 설치 방법(윈도우,리눅스 공통) : pip install {패키지명}
1.디지털타임스에 대한 뉴스 크롤링 코드
  - 디지털타임스의 특정 섹션 페이지(정치,경제,etc)의 URL을 입력하면 뉴스 리스트의 기사들을 읽고 지정한 날짜(default:오늘날짜)인 것만 크롤링한다
  - 결과는 json 파일로 저장한다
  - 크롤링 실행방법 : 코드 하단에서 getNewsDigitaltimes에 원하는 파라미터를 입력하여 실행한다
2.뉴스크롤링 결과 json 파일
  - digitaltimes.json 형태의 이름으로 저장된다
  - url         : 해당 뉴스 기사의 url주소
  - date        : 뉴스가 게재된 날짜
  - title       : 뉴스 타이틀
  - reporter    : 뉴스 게시자(기자)
  - body        : 뉴스 본문
"""

import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import datetime
import json
import re
# import os


# definition
NOT_FOUND = "NOT_FOUND"


# 주어진 url로부터 html응답 코드를 받아와 BeautifulSoup 타입으로 반환하는 함수
def getBeautifulSoup(url):
    response = requests.get(url)                    # 입력된 url로 request 요청 및 html 코드 수신
    response.encoding = 'euc-kr'                    # 디지털타임스는 한글 인코딩을 euc-kr로 사용함
    plainText = response.text                       # html 소스코드를 텍스트로 변환, utf-8로 인코딩
    soup = BeautifulSoup(plainText, "lxml")         # BeautifulSoup 객체로 보기 쉽게 변환하여 반환
    return soup


# 태그 트리 중에서 특정 태그(br 태그 등)들을 제거하는 함수
def removeTag(soup: BeautifulSoup, tag):
    for sp in soup.findAll(tag):
        sp.extract()                                # parent 태그로부터 현재 자식 태그들을 제거한다.


# 입력받은 태그들에서 href(대상 하이퍼링크) 경로를 추출하는 함수
def getHrefFromTag(tags):
    targetTag = tags.find('a', href=True)           # 태그 이름이 a인 것을 하나 추출
    return targetTag['href']                        # 태그 내의 href 필드 값을 반환


# href가 가리키는 뉴스기사 페이지로부터 뉴스 타이틀 추출하는 함수
def getTitleFromHref(soup: BeautifulSoup):
    contentWrapTag = soup.select(".cntWrap")[0]                 # 뉴스본문을 담고있는 태그 트리 추출
    upperTableTag = contentWrapTag.find(id="news_names")        # 본문 중 상단 테이블 태그 트리 추출
    h1Tag = upperTableTag.find("h1")                            # h1 태그를 추출(타이틀 태그)
    if len(h1Tag) > 0:                                          # 빈 내용에 대한 예외처리
        titleList = h1Tag.findAll(text=True, recursive=True)    # 타이틀 문자열 추출(list)
        title = ''.join(titleList)                              # list to string
        return title
    return NOT_FOUND


# href가 가리키는 뉴스기사 페이지로부터 뉴스 본문을 추출하는 함수
def getBodyFromHref(soup: BeautifulSoup):
    articleTag = soup.find(id="NewsAdContent")                  # 뉴스기사 본문에 해당하는 태그 트리 추출
    removeTag(articleTag, 'br')                                 # step1으로부터 불필요한 br 태그들 제거
    textList = articleTag.findAll(text=True, recursive=True)    # 태그들로부터 텍스트 내용만 재귀적으로 추출한 리스트
    fullText = ''.join(textList)                                # list to string
    return fullText


# href가 가리키는 뉴스기사 페이지로부터 뉴스 일자를 추출하는 함수
def getTimeFromHref(soup: BeautifulSoup, date):
    contentWrapTag = soup.select(".cntWrap")[0]                 # 뉴스본문을 담고있는 태그 트리 추출
    upperTableTag = contentWrapTag.find(id="news_names")        # 본문 중 상단 테이블 태그 트리 추출
    pTag = upperTableTag.find("p")                              # p 태그를 추출(기자-날짜 태그)
    if len(pTag) > 0:                                           # 빈 내용에 대한 예외처리
        downList = pTag.findAll(text=True, recursive=True)      # 기자-날짜 문자열 추출(list)
        downStr = ''.join(downList)                             # list to string
        timeSearch = re.search("[0-9]{4}-[0-9]{2}-[0-9]{2}", downStr)
        if timeSearch is not None:
            time = timeSearch.group()   # 정규표현식으로 날짜만 추출
            if len(time) > 0:
                return time
    # return NOT_FOUND
    return date


# href가 가리키는 뉴스기사 페이지로부터 뉴스 게시자를 추출하는 함수
def getReporterFromHref(soup: BeautifulSoup, date):
    contentWrapTag = soup.select(".cntWrap")[0]                 # 뉴스본문을 담고있는 태그 트리 추출
    upperTableTag = contentWrapTag.find(id="news_names")        # 본문 중 상단 테이블 태그 트리 추출
    pTag = upperTableTag.find("p")                              # p 태그를 추출(기자-날짜 태그)
    if len(pTag) > 0:                                           # 빈 내용에 대한 예외처리
        downList = pTag.findAll(text=True, recursive=True)      # 기자-날짜 문자열 추출(list)
        downStr = ''.join(downList)                             # list to string
        deltime = re.sub(r"[0-9]{2}:[0-9]{2}", '', downStr)
        reporter = deltime.replace('입력', '')\
            .replace(date, '')\
            .replace('|', '')\
            .replace(':','')    # 기자 이외 문자열 제거
        if len(reporter) > 0 and re.search("[^ ]", reporter) is not None:
            return reporter
    return NOT_FOUND


# 지정된 json 파일명으로 데이터 저장하는 함수
def appendDataToJsonFile(data, filename):
    with open('data/'+filename, 'a', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
        f.write('\n')       # 각 json 데이터 사이 띄워서 저장하기
        f.close()


"""
[핵심 함수] 디지털타임스의 특정 섹션 페이지에서 뉴스를 크롤링하여 json으로 저장하는 함수
  - url         : 대상 뉴스 웹 URL. 섹션 메뉴 클릭 시 접속하게 되는 뉴스 리스트 URL을 의미
  - filename    : 결과를 저장할 json 파일명
  - date        : 크롤링할 뉴스의 일자(예시 '2017-12-05') (default: 금일 날짜)
  - maxpage     : 읽어올 총 페이지 수. 1페이지부터 읽어옴. (default: 5)
  - isTestmode  : 실행 결과를 표준출력으로 보고자 할 때 True로 입력. (default: False)
"""
def getNewsDigitaltimes(url, filename, date="", maxpage=5, isTestmode=False):

    # 뉴스 일짜 미입력 시 오늘 날짜로 설정 (예시 '2017-12-05')
    if date == "": date = datetime.datetime.now()
    else: date = datetime.datetime.strptime(date, '%Y-%m-%d')

    page = 1    # 페이지 인덱스 초기화

    # 주어진 페이지 수만큼 반복
    while page <= maxpage:
        # 현재 페이지의 url 생성
        current_url = url + '&mode=concrete&cpage=' + str(page) \
                      + '&sel_y=' + str(date.year) \
                      + '&sel_m=' + str(date.month).zfill(2) \
                      + '&sel_d=' + str(date.day).zfill(2)

        soup = getBeautifulSoup(current_url)            # 현재 페이지의 html을 추출
        newsListTag = soup.select(".contents")          # 섹션의 뉴스 리스트를 담고 있는 태그트리 추출
        newsPageTag = soup.select(".page_num")          # 섹션의 하단에 뉴스 페이지 번호들을 담고 있는 태그트리 추출

        # 읽을 수 있는 페이지가 더 없을 경우 예외처리
        if len(newsPageTag) < page:
            print("[INFO] All pages crawling finished")
            return

        print("[INFO] now page : ", page)

        # 뉴스 리스트가 비어있을 경우 예외처리
        if len(newsListTag) <= 0:
            print("[ERROR] News list doesn't have any item..")
            return

        for tag in newsListTag[0].select(".concrete"):
            data = {}                                   # 파일 덤프를 위한 buffer
            href = getHrefFromTag(tag)                  # 각 기사의 href(대상 하이퍼링크 주소) 추출
            hrefSoup = getBeautifulSoup(href)           # 추출한 href에 대해 다시 html정보 추출
            newsDate = getTimeFromHref(hrefSoup, date.strftime("%Y-%m-%d"))        # 추출한 href에 대해 뉴스 일자를 추출 (YYYY-MM-dd)

            # 대상 날짜의 뉴스기사가 더 이상 없을 경우
            if newsDate > '{0:%Y-%m-%d}'.format(date):
                # print("\n[FINISHED] No more news! (page:", page, ")\n")
                return

            # 대상 날짜와 읽어온 뉴스 게시일 동일할 경우에만 이하를 수행
            elif newsDate == '{0:%Y-%m-%d}'.format(date):
                # json 파일 dump를 위한 key-value 쌍 입력
                data['url'] = href
                data['date'] = newsDate
                data['title'] = getTitleFromHref(hrefSoup)                  # 추출한 href에 대해 뉴스 타이틀 추출
                data['reporter'] = getReporterFromHref(hrefSoup, newsDate)  # 추출한 href에 대해 뉴스 게시자를 추출
                data['body'] = getBodyFromHref(hrefSoup)                    # 추출한 href에 대해 뉴스 본문을 추출

                if isTestmode:
                    print("=========================================================================")
                    print(">> URL      : ", data['url'])
                    print(">> date     : ", data['date'])
                    print(">> title    : ", data['title'])
                    print(">> reporter : ", data['reporter'])
                    print(">> body \n", data['body'])

                # 크롤링 결과를 json 파일에 저장하기(append)
                appendDataToJsonFile(data, filename)

        # 다음 페이지 읽기
        page += 1


# --------------------------------------------------------------------------------------
# ------------------------------------- Main Field -------------------------------------
# --------------------------------------------------------------------------------------

# (1) 위에서 정의한 함수를 호출하여 내일신문에 대한 뉴스 크롤링을 실행한다.

sectionUrl1 = 'http://www.dt.co.kr/article_list.html?gcd=1&scd=100&lcd=2401' # 정치 섹션
sectionUrl2 = 'http://www.dt.co.kr/article_list.html?gcd=1&scd=100&lcd=2001' # 정보통신컨텐츠
sectionUrl3 = 'http://www.dt.co.kr/article_list.html?gcd=1&scd=100&lcd=2201' # 산업
sectionUrl4 = 'http://www.dt.co.kr/article_list.html?gcd=1&scd=100&lcd=2101' # IT중기
sectionUrl5 = 'http://www.dt.co.kr/article_list.html?gcd=1&scd=100&lcd=2801' # 과학유통건설
sectionUrl6 = 'http://www.dt.co.kr/article_list.html?gcd=1&scd=100&lcd=3101' # 경제금융증권
sectionUrl7 = 'http://www.dt.co.kr/article_list.html?gcd=1&scd=100&lcd=2501' # 문화연예
sectionUrl8 = 'http://www.dt.co.kr/article_list.html?gcd=1&scd=100&lcd=0201' # 오피니언
sectionList = [sectionUrl1, sectionUrl2, sectionUrl3, sectionUrl4,
               sectionUrl5, sectionUrl6, sectionUrl7, sectionUrl8]


# 뉴스 크롤링 실행 (하루치만 크롤링할 떄 다음 명령어 실행)
# getNewsDigitaltimes(url=targetUrl,                  # param 1) 내일신문 섹션 별 url. 읽어올 섹션 URL만 주석을 해제한다.
#                     filename='digitaltimes.json',   # param 2) 뉴스 크롤링 결과를 저장할 파일명. json 포맷으로 저장
#                     date='2012-12-29',              # param 3) 크롤링할 뉴스 날짜 (default: 금일)
#                     #maxpage=5,                     # param 4) 읽어올 뉴스 페이지 수 (default: 5)
#                     isTestmode=True)                # param 5) 표준출력으로 결과 보려면 True (default: False)


# datetime을 이용하여 특정 일수 동안의 뉴스 데이터를 크롤링한다
begin_str = "2018-01-18"                                        # 크롤링일 시작할 날짜. 이날부터 하루씩 과거로 진행
begin_dt = datetime.datetime.strptime(begin_str, "%Y-%m-%d")    # 시작일을 datetime 포맷으로 변경

max_days = 365     # 크롤링할 일수
for i in range(max_days):
    target_dt = (begin_dt - datetime.timedelta(days=i)).strftime("%Y-%m-%d")        # 대상일 계산
    # 섹션별로 해당 날짜별로 하루치씩 크롤링
    for section in sectionList:
        getNewsDigitaltimes(url=section, filename='digitaltimes.json', date=target_dt, isTestmode=True)


# (2) Main Field에서 실행한 결과 파일을 읽어 표준출력하여 확인한다.

# # 저장된 json 파일 열어서 json 리스트로 읽기
# with open('digitaltimes.json', encoding='utf-8') as fp:
#     loadedList = [json.loads(line) for line in fp]      # json 데이터들의 리스트
#
# # 읽은 json 리스트 출력하기
# for line in loadedList:
#     print(line)
#
# print(" * json 리스트 중 0번째 라인, 'url' 필드값 읽기 -> ", loadedList[0]['url'])
