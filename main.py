# coding=UTF-8
from filelock import  FileLock
import os

os.chdir(path)
lock=FileLock('lock',timeout=1)

#检查临时文件
if_file_exist:list=[]
if os.path.exists('video_temp.m4s'):
    if_file_exist.append('video_temp.m4s')
if os.path.exists('audio_temp.m4s'):
    if_file_exist.append('audio_temp.m4s')
if len(if_file_exist)>0:
    answer=input('存在临时文件，是否删除：')
    if answer=='y':
        for i in if_file_exist:
            os.remove(i)
            print('好的，删除临时文件')
        else:
            exit('你选择直接退出')

import asyncio
from bilibili_api import video, Credential, HEADERS, sync, favorite_list
import httpx
import json
from tqdm.asyncio import tqdm_asyncio
import re

'''
注意需要配置的变量
path：路径，请安排一个单独文件夹
credential：登录用，不登录请改为None
media_id：收藏夹id

'''
path=''
credential = Credential(sessdata='', bili_jct='', buvid3='')
media_id:int=


def download_url(url:str,out:str,info:str) -> None :
    with httpx.stream("GET", url, headers=HEADERS) as response:
        # 获取文件大小
        print('正在下载：'+info)
        file_size = int(response.headers.get("Content-Length", 0))

        with open(out, "wb") as f:
            bytes_read = 0
            pbar = tqdm_asyncio(total=file_size, unit="B", unit_scale=True)

            for chunk in response.iter_bytes(1024*1024):
                f.write(chunk)
                bytes_read += len(chunk)
                pbar.update(len(chunk))
                #下载限速
                #await asyncio.sleep(0.3)

            pbar.close()


async def download_by_bv(bv) -> None:
    # 实例化 Credential 类
    global credential
    # 实例化 Video 类
    v = video.Video(bvid=bv,credential=credential)
    #v = video.Video(bvid=bv)
    # 获取视频下载链接
    title=await v.get_info()
    title=title['title']
    download_url_data = await v.get_download_url(0)
    # 解析视频下载信息
    detecter = video.VideoDownloadURLDataDetecter(data=download_url_data)
    streams = detecter.detect_best_streams(video_max_quality=video.VideoQuality._1080P)
    # print(streams, detecter)
    # 有 MP4 流 （有无音频）/ FLV 流三种可能
    name:str = f"{title}.{bv}.mp4"
    name = re.sub('[\/:*?"<>|]', "_", name)
    if detecter.check_flv_stream() == True:
        # FLV 流下载
        download_url(streams[0].url, "flv_temp.flv", "flv流："+name)
        # 转换文件格式
        os.system(f'ffmpeg -i flv_temp.flv -c:v copy -codec copy {name}')
        # 删除临时文件
        os.remove("flv_temp.flv")
    else:
        if streams[1]!=None:
            # MP4 流下载
            download_url(streams[0].url, "video_temp.m4s", "视频流:"+name)
            download_url(streams[1].url, "audio_temp.m4s", "音频流")
            # 混流
            os.system(f'ffmpeg -i audio_temp.m4s -i video_temp.m4s -c:v copy -codec copy "{name}"')
            # 删除临时文件
            os.remove("video_temp.m4s")
            os.remove("audio_temp.m4s")
        else:
            download_url(streams[0].url, "video_temp.m4s", "视频流"+name)
            os.system(f'ffmpeg -i video_temp.m4s -c:v copy -codec copy "{name}"')
            os.remove("video_temp.m4s")

    print(f"已下载为： {name}")

async def get_favo_list_online(media_id:int) -> list:
    global credential
    a = favorite_list.FavoriteList(media_id=media_id,credential=credential)
    b = await a.get_content_ids_info()
    li_get=[i['bvid'] for i in b]
    return li_get

def get_favo_list_peocessed() -> list:
    li_raw = os.listdir(os.getcwd())
    li_now = []
    for i in li_raw:
        a = i.split(".")
        if len(a) >= 3:
            li_now.append(a[-2])
    return li_now

async def get_favo_list_rest(media_id:int) -> list:
    favo_list_online=await get_favo_list_online(media_id)
    favo_list_processed=get_favo_list_peocessed()
    favo_list_rest=[i for i in favo_list_online if i not in favo_list_processed]
    return favo_list_rest

async def main(media_id:int) -> None:
    global lock
    if os.path.exists("tasks.json"):
        with open('tasks.json',mode='r') as fp:
            tasks=json.load(fp)
            favo_list_peocessed=get_favo_list_peocessed()
            tasks=[i for i in tasks if i not in favo_list_peocessed]
    else:
        tasks=await get_favo_list_rest(media_id)
        with open('tasks.json',mode='w') as fp:
            json.dump(tasks,fp)
        print("新任务")
    if len(tasks)==0:
        await asyncio.sleep(0.1)
        os.remove('tasks.json')
        exit('没有任务')
    print('任务队列：'+str(len(tasks)))
            
    tasks_copy=tasks.copy()
    for i in range(len(tasks)):
        print("开始下载" + str(tasks[i]))
        await download_by_bv(tasks[i])
        tasks_copy.remove(tasks[i])
        with open('tasks.json',mode='w') as fp:
            json.dump(tasks_copy,fp)
        print("下载结束" + str(tasks[i]))

    print('下载结束')

if __name__ == "__main__":
    with lock:
        sync(main(media_id))
