# coding: utf-8
import os
import requests
from bs4 import BeautifulSoup
import difflib as diff
import slackweb
import boto3
import configparser
from urllib.parse import urljoin

target_url = 'https://www.i.u-tokyo.ac.jp/edu/entra/index.shtml'
file_prev = '/tmp/prev.html'
file_now = '/tmp/now.html'
parser = 'html5lib'  # aws lambda doesn't support 'lxml'

s3_resource = boto3.resource('s3')
s3_client = boto3.client('s3')


def test_notify(event, context):
    send_message(event)
    return


def load_params():
    config_ini = configparser.ConfigParser()
    config_ini.read('config/asahi.ini', encoding='utf-8')
    global webhook_url, file_s3, bucket_name
    webhook_url = config_ini['slack']['webhook_url']
    bucket_name = config_ini['s3']['bucket_name']
    file_s3 = config_ini['s3']['file_s3']


def init():
    if not os.path.isdir('/tmp'):
        os.mkdir('/tmp')

    load_params()
    result = s3_client.list_objects(Bucket=bucket_name, Prefix=file_s3)["Contents"]
    if not len(result) > 0:
        soup = get_soup(target_url)
        save_soup(soup)
    print('init done.')


def save_soup(soup):
    with open(file_now, encoding='utf-8', mode='w') as f:
        f.write(str(soup))
    upload_soup()
    print('save done.')


def upload_soup():
    s3_resource.Bucket(bucket_name).upload_file(file_now, file_s3)
    print('upload done.')


def download_soup():
    s3_resource.Bucket(bucket_name).download_file(file_s3, file_prev)
    print('download done.')


def get_soup(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.content, parser, from_encoding='utf-8')
    print('get latest html.')
    return soup.find('div', id='free')


def get_message(lines_prev, lines_now):
    messages = list()
    diff1 = [line[1:] for line in diff.unified_diff(lines_now, lines_prev) if line[0] == '-']
    if len(diff1) < 1:
        return ''
    for line in diff1[1:]:
        soup = BeautifulSoup(line, parser)
        links = soup.find_all('a')
        urls = list()
        for link in links:
            url = link.get('href')
            if url[0:4] != 'http':
                url = urljoin(target_url, url)
            urls.append(url)
        if not soup.get_text() and len(urls) == 0:
            continue
        messages.append(soup.get_text())
        messages.extend(urls)
        messages.append('')
    return '\n'.join(messages[:-1])


def send_message(message):
    slack = slackweb.Slack(url=webhook_url)
    slack.notify(text=message)


def lambda_handler(event, context):
    init()

    # get prev html
    download_soup()
    with open(file_prev, encoding='utf-8') as f:
        txt_prev = f.read()
    soup_prev = BeautifulSoup(txt_prev, parser)
    lines_prev = [line.strip() for line in str(soup_prev).splitlines()]

    # get now html
    soup_now = get_soup(target_url)
    lines_now = [line.strip() for line in str(soup_now).splitlines()]

    message = get_message(lines_prev, lines_now)
    if message:
        prefix = '冬優子ちゃん大変っす！院試情報が更新されたっすよ！\n'
        send_message(prefix + target_url + '\n\n' + message)
        print(prefix + target_url + '\n\n' + message)

        save_soup(soup_now)

    return


if __name__ == '__main__':
    lambda_handler(None, None)
