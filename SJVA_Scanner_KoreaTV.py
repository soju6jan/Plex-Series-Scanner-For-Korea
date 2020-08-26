# -*- coding: UTF-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import re, os, os.path
import Media, VideoFiles, Stack, Utils
import time, json, traceback, io

episode_regexps = [
    r'\.([sS](?P<season>[0-9]{1,2}))?[eE](?P<ep>[0-9]{1,4})'
]

date_regexps = [
    r'[^0-9a-zA-Z](?P<year>[0-9]{2})(?P<month>[0-9]{2})(?P<day>[0-9]{2})[^0-9a-zA-Z]', # 6자리
    r'(?P<year>[0-9]{4})[^0-9a-zA-Z]+(?P<month>[0-9]{2})[^0-9a-zA-Z]+(?P<day>[0-9]{2})([^0-9]|$)',  # 2009-02-10 
]

try:
    import logging
    import logging.handlers
    logger = logging.getLogger('sjva_scanner')
    logger.setLevel(logging.DEBUG) 
    formatter = logging.Formatter(u'[%(asctime)s|%(levelname)s] : %(message)s')
    #file_max_bytes = 10 * 1024 * 1024 
    filename = os.path.join(os.path.dirname( os.path.abspath( __file__ ) ), '../../', 'Logs', 'sjva.scanner.korea.tv.log')
    fileHandler = logging.FileHandler(filename, encoding='utf8')
    #fileHandler = logging.handlers.RotatingFileHandler(filename=filename), maxBytes=file_max_bytes, backupCount=5, encoding='euc-kr')
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)
except:
    pass

def Scan(path, files, mediaList, subdirs, language=None, root=None):
    VideoFiles.Scan(path, files, mediaList, subdirs, root)
    paths = Utils.SplitPath(path)
    shouldStack = True
    logger.debug('=====================================================')
    logger.debug('- path:%s' % path)
    logger.debug('- files count:%s' % len(files))
    logger.debug('- subdir count:%s' % len(subdirs))
    for _ in subdirs:
        logger.debug(' * %s' % _)
    if len(paths) != 0:
	    logger.debug('- paths[0] : %s' % paths[0])
    if len(paths) == 1 and len(paths[0]) == 0:
        return
    name, year_path = VideoFiles.CleanName(paths[0])
    tmp = os.path.split(path)
    logger.debug(tmp)
    season_num = None
    if len(tmp) == 2 and tmp[0] != '': 
        try:
            match = re.search(r'(?P<season_num>\d{1,4})\s*((?P<season_title>.*?))?', tmp[1], re.IGNORECASE)
            if match:
                season_num = match.group('season_num')
                logger.debug('- season_num:%s', season_num)
        except:
            season_num = None
    logger.debug('- show(by path) name:%s year:%s', name, year_path)
    logger.debug('- files count : %s', len(files))
    for i in files:
        tempDone = False
        try:
            file = os.path.basename(i)
            logger.debug(' * FILE : %s' % file)
            for rx in episode_regexps:
                match = re.search(rx, file, re.IGNORECASE)
                if match:
                    # 파일명에 시즌 번호가 있다면 파일명 우선
                    if match.group('season') is not None:
                        season = int(match.group('season'))
                    else:
                        #파일명에 시즌표시가 없다.
                        if season_num is not None:  # 폴더에 시즌 번호가 있다면..
                            season = season_num
                        else:
                            season = 1
                    episode = int(match.group('ep'))
                    tv_show = Media.Episode(name, season, episode, '', year_path)
                    tv_show.display_offset = 0
                    tv_show.parts.append(i)
                    mediaList.append(tv_show)
                    logger.debug('  - APPEND by episode: %s' % tv_show)
                    tempDone = True
                    break
            if tempDone == False:
                for rx in date_regexps:
                    match = re.search(rx, file)
                    if match:
                        year = match.group('year')
                        year = int(year) + 2000 if len(year) == 2 else int(year)
                        month = int(match.group('month'))
                        day = int(match.group('day'))
                        tmp = '%d-%02d-%02d' % (year, month, day)
                        if season_num is None:
                            tv_show = Media.Episode(name, year, None, None, None)
                        else:
                            tv_show = Media.Episode(name, season_num, None, None, None)
                        #tv_show = Media.Episode(name, year, tmp, None, year)
                        tv_show.released_at = tmp
                        tv_show.parts.append(i)
                        mediaList.append(tv_show)
                        logger.debug('  - APPEND by date: %s' % tv_show)
                        tempDone = True
                        break
            if tempDone == False:
                logger.debug(' NOT APPEND!!')
        except Exception, e:
            logger.error(e)
    if shouldStack:
        Stack.Scan(path, files, mediaList, subdirs)

