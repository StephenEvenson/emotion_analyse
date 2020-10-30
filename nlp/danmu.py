import csv
import jiagu
import jieba
import pandas as pd
import pymongo
import re
import requests
import time
import json
from bs4 import BeautifulSoup as BS
from selenium import webdriver

from db.config import DB_URI, DB_NAME


def get_aid(url, space, info):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.103 Safari/537.36'
    }
    response = requests.get(url=url, headers=headers)
    json = response.json()
    if info:
        print(json)
        space['up'] = json['data']['list']['vlist'][0]['author']
        space['all_count'] = json['data']['page']['count']
    for v in json['data']['list']['vlist']:
        space['vlist'].append({'aid': 'av' + str(v['aid'])})
    return space


def open_space(space_url, num=-1):
    space = {'vlist': []}
    base_url = 'https://api.bilibili.com/x/space/arc/search?mid={mid}&ps=5&pn={page}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.103 Safari/537.36'
    }
    uuid = space_url.lstrip('https://space.bilibili.com/')
    space['uuid'] = uuid
    url = base_url.format(mid=uuid, page=1)
    get_aid(url, space, True)
    page_num = int(space['all_count'] / 5) + 1
    for i in range(2, page_num + 1, 1):
        if 0 <= num < (i - 1) * 5:
            break
        url = base_url.format(mid=uuid, page=i)
        get_aid(url, space, False)
    return space


# 打开网页函数
def open_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.103 Safari/537.36'
    }
    response = requests.get(url=url, headers=headers)
    response.encoding = 'utf-8'
    html = response.text
    return html


# 获取弹幕url中的数字id号

# 当requests行不通时，采用selenium的方法。
def sele_get(url):
    SERVICE_ARGS = ['--load-images=false', '--disk-cache=true']
    driver = webdriver.PhantomJS(service_args=SERVICE_ARGS)
    driver.get(url)
    time.sleep(2)
    danmu_id = re.findall(r'cid=(\d+)&', driver.page_source)[0]

    return danmu_id


def get_danmu_id(html, url):
    try:
        soup = BS(html, 'html.parser')
        # 视频名
        title = soup.select('title[data-vue-meta="true"]')[0].get_text().rstrip('_哔哩哔哩 (゜-゜)つロ 干杯~-bilibili')

        # 投稿人
        author = soup.select('meta[name="author"]')[0]['content']
        # 弹幕的网站代码
        try:
            danmu_id = re.findall(r'cid=(\d+)&', html)[0]
            # danmu_id = re.findall(r'/(\d+)-1-64', html)[0]
            # print(danmu_id)
        except:
            danmu_id = sele_get(url)
        print(title, author)
        return danmu_id, title, author
    except:
        print('视频不见了哟')
        return False, False, False


# 秒转换成时间
def sec2str(seconds):
    seconds = eval(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    time = "%02d:%02d:%02d" % (h, m, s)
    return time


# csv保存函数
def csv_write(table_list, table_header, path):
    # table_header = ['出现时间', '弹幕模式', '字号', '颜色', '发送时间', '弹幕池', '发送者id', 'rowID', '弹幕内容']
    with open(path, 'w', newline='', errors='ignore') as f:
        writer = csv.writer(f)
        if table_header:
            writer.writerow(table_header)
        for row in table_list:
            writer.writerow(row)


def text_write(table_list, table_header, path):
    with open(path, 'w', newline='', errors='ignore') as f:
        if len(table_header) > 0:
            f.writelines(table_header)
            f.write('\n')
        for row in table_list:
            f.write(row + '\n')


def dict_write(dict_content, path):
    with open(path, 'w') as f:
        json.dump(dict_content, f, ensure_ascii=False)


def dict_read(path):
    with open(path, "r") as f:
        dic = json.load(f)
    return dic


def insert_video(video):
    client = pymongo.MongoClient(DB_URI)
    db = client[DB_NAME]
    collection = db['video']
    collection.find_one_and_delete({'id': video['id']})
    result = collection.insert(video)
    print(result)


def check_comment(url, video):
    table_header = ['appearance', '弹幕模式', '字号', '颜色', '发送时间', '弹幕池', '发送者id', 'rowID', 'content', 'emotion']
    video_url = url
    video_html = open_url(video_url)
    danmu_id, video['title'], video['up'] = get_danmu_id(video_html, video_url)
    all_list = []
    if danmu_id:
        danmu_url = 'http://comment.bilibili.com/{}.xml'.format(danmu_id)
        danmu_html = open_url(url=danmu_url)
        soup = BS(danmu_html, 'html.parser')
        all_d = soup.select('d')
        for d in all_d:
            # 把d标签中P的各个属性分离开
            danmu_list = d['p'].split(',')
            # d.get_text()是弹幕内容
            danmu_list.append(d.get_text())
            nature, value = jiagu.sentiment(danmu_list[8])
            if nature == 'negative':
                value = - value
            danmu_list.append(value)
            # danmu_list[0] = sec2str(danmu_list[0])
            # danmu_list[4] = time.ctime(eval(danmu_list[4]))
            all_list.append(danmu_list)
            # print(danmu_list)
        # all_list.sort()
        df = pd.DataFrame(all_list, columns=table_header)
        video_df = df.iloc[:, [0, 7, 8, 9]]
        bullet_screen_count = video_df.shape[0]
        # danmu_emotion = video_df.to_dict(orient='records')
        if 'id' in video:
            id = 'id'
        else:
            id = 'aid'
        # dict_write(dict_content=danmu_emotion, path='screen_bullet/danmu_emotion/{}.csv'.format(video[id]))
        video_df.to_csv('screen_bullet/danmu_emotion/{}.csv'.format(video[id]))
        # video['danmu'] = danmu_emotion
        video['count'] = bullet_screen_count
    return video, danmu_id, video_df.iloc[:, 2]


def word_frequency(video_id):
    with open('screen_bullet/{}.csv'.format(video_id), 'r') as f:
        danmu_content = f.read()
    jieba.add_word('卧槽')
    jieba.add_word('高能')
    jieba.add_word('护体')
    stopwords = set()
    stopwords.update(['哈', '哈哈', '哈哈哈', '哈哈哈哈', '啊',
                      '啊啊', '啊啊啊', '啊啊啊啊', '没有', '真的',
                      '就是', '什么', '不是', '这么', '自己',
                      '不会', '这个', '怎么', '觉得', '一个',
                      '有点', '那么', '你们', '一样', '还是',
                      '还有', '已经', '知道', '是不是', '那个',
                      '可以', '不能', '时候', '感觉', '这样',
                      '好像', '因为', '现在', '不要', '哈哈哈哈哈',
                      '哈哈哈哈哈哈', '为什么', '了我', '我们', '下次', '奥利'])
    words = jieba.lcut(danmu_content)
    word_count = {}
    word_counts = []
    for word in words:
        if word not in stopwords:
            # 不统计字数为一的词
            if len(word) >= 6 or len(word) == 1:
                continue
            else:
                word_count[word] = word_count.get(word, 0) + 1
    for k, v in word_count.items():
        word = {'name': k, 'value': v}
        word_counts.append(word)
    # text_write(table_list=word_count, table_header=[], path='screen_bullet/word_fq/{}.csv'.format(video_id))
    dict_write(dict_content=word_counts, path='screen_bullet/word_fq/{}.csv'.format(video_id))
    # print(word_count)
    return word_count
    # print(sorted(word_count.items(), key=lambda item: item[1]))


def assess_comment(url):
    videos = {}
    video = {'id': url.lstrip('https://www.bilibili.com/video/')}
    video, danmu_id, danmu_content = check_comment(url=url, video=video)
    text_write(table_list=danmu_content, table_header=[], path='screen_bullet/{}.csv'.format(video['id']))
    word_frequency(video['id'])
    # dict_write(dict_content=video, path='test/test.csv')
    # if danmu_id:
    #     insert_video(video)
    videos['up'] = video['up']
    videos['count'] = 1
    videos['vlist'] = []
    videos['vlist'].append(video)
    dict_write(dict_content=videos, path='screen_bullet/base/{}.csv'.format(video['id']))
    return danmu_id


def get_word_frequency(id):
    word_fq = dict_read(path='screen_bullet/word_fq/{}.csv'.format(id))
    count = len(word_fq)
    return word_fq, count


def single_video_wf(url):
    vid = url.lstrip('https://www.bilibili.com/video/')
    word_fq, count = get_word_frequency(vid)
    base = dict_read(path='screen_bullet/base/{}.csv'.format(vid))
    base['vlist'][0]['word_fq'] = word_fq
    base['vlist'][0]['count'] = count
    return base


def judge_url_type(url):
    video_base = "https://www.bilibili.com/video/"
    space_base = "https://space.bilibili.com/"
    matchObj_video = re.match(video_base, url)
    matchObj_space = re.match(space_base, url)
    if matchObj_video:
        return 1
    elif matchObj_space:
        return 2
    else:
        return 0


def assess_all_comment(url, num=-1):
    space = open_space(url, num=num)
    count = 0
    is_exist = True
    for v in space['vlist']:
        if num >= 0 and count == num:
            break
        url = 'https://www.bilibili.com/video/{}'.format(v['aid'])
        video, danmu_id, danmu_content = check_comment(url, v)
        text_write(table_list=danmu_content, table_header=[], path='screen_bullet/{}.csv'.format(v['aid']))
        word_frequency(v['aid'])
        count += 1
    if num == -1:
        space['count'] = space['all_count']
    else:
        space['count'] = num
    dict_write(dict_content=space, path='screen_bullet/base/{}.csv'.format(space['uuid']))
    if len(space['vlist']) == 0:
        is_exist = False
    return is_exist


def space_video_wf(url):
    uuid = url.lstrip('https://space.bilibili.com/')
    base = dict_read(path='screen_bullet/base/{}.csv'.format(uuid))
    for v in base['vlist']:
        if 'title' in v:
            aid = v['aid']
            word_fq, count = get_word_frequency(aid)
            v['word_fq'] = word_fq
            v['count'] = count
    base['vlist'] = list(filter(lambda x: 'title' in x, base['vlist']))
    return base


#### 表格制作


def get_diagram(id):
    diagram_data = pd.read_csv('screen_bullet/danmu_emotion/{}.csv'.format(id), usecols=[1, 2, 3, 4])
    return diagram_data


def make_diagram(data, n):
    diagram = {}
    max_time = data['appearance'].max()
    num = int(max_time / n / 10) + 1
    interval = num * 10
    duration = interval * n
    diagram['duration'] = duration
    diagram['interval'] = num * 10
    diagram['n'] = n
    diagram['sum'] = []
    diagram['average'] = []
    diagram['pos'] = []
    diagram['neg'] = []
    for i in range(n):
        inter = data[data['appearance'].apply(lambda x: i * interval < x <= (i + 1) * interval)]
        emo_sum = inter['emotion'].sum()
        emo_ave = emo_sum / inter['emotion'].count()
        emo_pos = inter[inter['emotion'].apply(lambda x: x > 0)]['emotion'].count()
        emo_neg = inter[inter['emotion'].apply(lambda x: x <= 0)]['emotion'].count()
        diagram['sum'].append(format(emo_sum, '0.2f'))
        diagram['pos'].append(int(emo_pos))
        diagram['neg'].append(int(emo_neg))
        diagram['average'].append(format(emo_ave, '0.2f'))
    return diagram


def single_video_dg(url, n=5):
    vid = url.lstrip('https://www.bilibili.com/video/')
    diagram_data = get_diagram(vid)
    base = dict_read(path='screen_bullet/base/{}.csv'.format(vid))
    diagram = make_diagram(diagram_data, n)
    base['vlist'][0]['diagram'] = diagram
    return base


def space_video_dg(url, n=5):
    uuid = url.lstrip('https://space.bilibili.com/')
    base = dict_read(path='screen_bullet/base/{}.csv'.format(uuid))
    for v in base['vlist']:
        if 'title' in v:
            aid = v['aid']
            diagram_data = get_diagram(aid)
            diagram = make_diagram(diagram_data, n)
            v['diagram'] = diagram
    base['vlist'] = list(filter(lambda x: 'title' in x, base['vlist']))
    return base
