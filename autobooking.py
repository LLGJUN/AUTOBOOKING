#-*- coding: utf-8 -*-#
#中大东校区体育馆羽毛球场地自动订场软件
#可以输入预期订场地个数，定场时间段
#订场策略优化？？ 同时开两个浏览器，多线程操作，每个时间段一个线程
#支持提前运行代码，定时抢场地

from splinter.browser import Browser
from datetime import datetime,timedelta
import time
import re
import threading
import ConfigParser



#根据订场时间段返回场地号的起始id 场地有15个
#周一到周五 时间段为18:01-22:00  周末时间段为09:01-22:00
#book_time代表预定时间段，为字符串格式，isweekend 表示是否是周末，取值0或者1
def get_start_placeId_by_time(book_time):
    time_placeid_weekend = {
        '09:01-10:00':0,
        '10:01-11:00':15,
        '11:01-12:00':30,
        '14:01-15:00':45,
        '15:01-16:00':60,
        '16:01-17:00':75,
        '17:01-18:00':90,
        '18:01-19:00':105,
        '19:01-20:00':120,
        '20:01-21:00':135,
        '21:01-22:00':150}

    time_placeid_weekday = {
        '18:01-19:00': 0,
        '19:01-20:00': 15,
        '20:01-21:00': 30,
        '21:01-22:00': 45}

    if datetime.isoweekday(datetime.now() + timedelta(days=1))<= 5:  #周一到周五
        return time_placeid_weekday[book_time]
    else:
        return time_placeid_weekend[book_time]

#给定某个时间段目标场地集合，判断目标场地是否可以预定,返回可以预定的场地集合
#输入参数 placenum_set 目标场地号集合（1-15）,span span元素集合
def judge_aim_place_booking(start_place_id,placenum_set,span_set):
    update_place_set=[]
    for i in placenum_set:
        span_text=span_set[start_place_id+i-1].outer_html
        if span_text.find('lock')!=-1:
            #print i,'场地已经被预定'
            pass
        else:
            #print i,'号场地可以预定'
            update_place_set.append(i)
    return update_place_set

#登录预定系统
def login_booking(netidname,netidpwd):
    b = Browser()
    b.visit('http://gym.sysu.edu.cn/index.html')
    login = b.find_link_by_href("javascript:login();")  # 找到登录按钮
    login.click()

    # 输入账号密码和验证码
    b.fill('username', netidname)
    b.fill('password', netidpwd)
    validcode = raw_input('Please here enter the verification code of login interface manually:')
    b.fill('captcha', validcode)
    b.find_by_name('submit').click()  # 点击登录按钮
    return b

#从输入端获取时间段和场地信息
def get_message_from_input():
    # 选取预定时间
    my_time = raw_input('Please enter a booking period like 09:01-10:00:')
    # 选取预定的场地，放回值为一个元组
    my_place_num_set = input('Please enter the number of the site you want to reserve(1 to 15),your input can be like 3,4,5 and 0 means you can order any empty field:')
    if my_place_num_set == 0:
        my_place_num_set = (2,3,4,7,8,9,10,13,14,12,5)
    my_place_count=input('Please input the num of site you want to reserve(1 to 2) :')
    return my_time,my_place_num_set,my_place_count

#开始预定场地时的等待
def wait_for_booking(b):
    # b=Browser()
    dt = datetime.now()  # 获取目前时间点
    # now_time_str=dt.strftime('%y-%m-%d %I:%M:%S %p')  #15-03-08 11:30:42 PM
    daynum1 = int(dt.strftime('%j'))  # 刚运行程序日期是今年的第多少天
    istimeout=False
    while not istimeout:
        time.sleep(5)
        dt = datetime.now()  # 获取目前时间点
        daynum2 = int(dt.strftime('%j'))  # 循环过程日期是今年的第多少天
        b.visit('http://gym.sysu.edu.cn/product/show.html?id=35')  #刷新页面
        if daynum2-daynum1==1:
            print 'Now you can reserve badmition site'
            istimeout=True

#跳转到预定界面----先提取可以预定的场地列表，再预定场地,预订的场地在订单中，处于尚未支付状态
def start_booking(mybrower,my_time,my_place_num_set,my_place_count):

    #计算明天的日期
    detaday=timedelta(days=1)
    dt = datetime.now() #获取目前时间点
    da_days=dt+detaday
    booking_date=str(da_days.strftime('%Y-%m-%d'))

    start_place_id = get_start_placeId_by_time(my_time)  # 获取指定时间段场地号起始ID

    date_choice=[] #表示订场日期元素
    #判断是否刷出了场地日期选项
    while date_choice == []:
        mybrower.visit('http://gym.sysu.edu.cn/product/show.html?id=35')  # 跳转到东校区羽毛球场
         # mybrower.visit('http://gym.sysu.edu.cn/product/show.html?id=61')  #南校区羽毛球场
        #点击要订场的日期
        date_choice=mybrower.find_by_text(booking_date)
        time.sleep(2)

    # date_choice.click()
    # place_area=mybrower.find_by_id('places')          #定位到选取场地的区域
    # span_set=place_area.first.find_by_tag('span')     #选取场地信息，返回所有场地列表  返回值是一个场地元素数组
    # booking_place_id_set=judge_aim_place_booking(start_place_id,my_place_num_set,span_set)  #得到可以预定的场地集合
    # print 'This time period ',booking_date,' ',my_time,' you can choose these site：',booking_place_id_set
    # if len(booking_place_id_set)==0:
    #     #print 'The time period has been reserved all'
    #     return 0

    count=0 #统计订到的场地数
    book_place=[]

    for yourplace in my_place_num_set:
        # mybrower.visit('http://gym.sysu.edu.cn/product/show.html?id=35')  # 跳转到东校区羽毛球场
        # date_choice = mybrower.find_by_text(booking_date)
        date_choice.click()
        place_area = mybrower.find_by_id('places')  # 定位到选取场地的区域
        span_set = place_area.first.find_by_tag('span')  # 选取场地信息，返回所有场地列表  返回值是一个场地元素数组
        try:
            span_set[start_place_id+int(yourplace)-1].click()
            print '1、已经成功勾选场地',yourplace
            time.sleep(0.5)

            q=mybrower.find_by_id('reserve')   #在选取场地界面点击确认预定按钮
            q.click()  #点击预定
            print '2、已经点击确定按钮',yourplace
            time.sleep(0.5)

            # q=mybrower.find_by_text('确认')    #当多次选取场地时，或者场地已经被定了，会弹出确定按钮，提示只能一次选取一个场地
            # q.click()

            q=mybrower.find_by_id('reserve')  #确认预定按钮，提交订单界面
            q.click()
            print '3、已经点击确定预定按钮，已经预定了场地',yourplace

            q=mybrower.find_by_text('确认')    #现在去支付确认按钮
            q.click()

            print '4、已经点击现在去支付按钮',yourplace

            # p=mybrower.find_by_tag('li')      #提取支付选项按钮
            # # p[13].click()                   #运动时支付
            # p[14].click()                     #运动经费支付

            # q=mybrower.find_by_text('立即支付')   #最终支付按钮
            # q.click()

            count +=1
            book_place.append(int(yourplace))
            if count >= my_place_count:
                break                   #预定一个场地成功后就退出循环,可以控制订场个数
        except Exception as err:       #当操作出现异常时，继续下一个场地操作
            print err
            pass

        date_choice=[]
        while date_choice == []:
            mybrower.visit('http://gym.sysu.edu.cn/product/show.html?id=35')  # 跳转到东校区羽毛球场
            # 点击要订场的日期
            date_choice = mybrower.find_by_text(booking_date)
            time.sleep(1)

    print ''
    print '========================================================================================='
    print 'You have successfully reserve these',book_place,'site at',booking_date,my_time

#提取订单中的日期和时间点
def get_booking_time(html_str):
    mat = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", html_str)
    date_str=mat.group()
    mat = re.search(r"(\d{1,2}:\d{1,2}-\d{1,2}:\d{1,2})",html_str)
    time_str=mat.group()
    return date_str,time_str

#30分钟内要支付完毕，否则订单会取消
#判断定的的场次是否满足我们的要求，满足的话即立即付款，不满足的话就取消订单
def check_order(b):
    already_book_time_set={}  #用来存储时间和对应的记录ID关系

    #获取明天的日期信息，用来核对订单日期，以免发生错误
    detaday = timedelta(days=1)
    dt = datetime.now()  # 获取目前时间点
    da_days = dt + detaday
    booking_date = str(da_days.strftime('%Y-%m-%d'))

    b.visit('http://gym.sysu.edu.cn/order/myorders.html')       #进入订单页面
    # c = b.find_link_by_partial_href('javascript:myorderdetail')  #订单号查询
    # e = b.find_link_by_partial_href('myorder_view.html?')         #付款查询
    time.sleep(15)
    tr_set=b.find_by_tag('tr')
    #print len(tr_set)

    idset=[]

    #先找出可以支付的订单的编号
    for k in range(len(tr_set)):
        try:
            if tr_set[k].outer_html.find(u'未支付') > 0:
                idset.append(k)
        except Exception as err:  # 当操作出现异常时，继续下一个场地操作
            # print err
            continue
    #查找每一行
    for k in idset:
        b.visit('http://gym.sysu.edu.cn/order/myorders.html')  #重新进入订单页面
        time.sleep(15)
        tr_set = b.find_by_tag('tr')
        #print len(tr_set)
        try:
            #print tr_set[k].outer_html
            if tr_set[k].outer_html.find(u'未支付') >0:             #判断某一行是否有没支付情况
                #print '===============+++++++++++++++++++======'
                #定位到了没有支付的订单号
                p=tr_set[k].find_by_tag('a')                    #获取三个点击链接
                p[1].click()                                   #点击查看按钮，跳到付款页面
                date_str, time_str=get_booking_time(b.find_by_tag('tr')[1].outer_html) #找出订场的时间 <td>2018-05-19</td> <td>09:01-10:00</td>
                if date_str == booking_date:    #先判断日期是否符合
                    if not already_book_time_set.has_key(time_str):
                        already_book_time_set[time_str]=[k]
                    else:
                        already_book_time_set[time_str].append(k)
        except Exception as err:  # 当操作出现异常时，继续下一个场地操作
        # print err
            continue

    print already_book_time_set
    return already_book_time_set

def pay_for_order(b,already_book_time_set):
    keys=already_book_time_set.keys()
    for key in keys:
        idset=already_book_time_set[key]
        id=idset[len(idset)/2]

        b.visit('http://gym.sysu.edu.cn/order/myorders.html')  # 进入订单页面
        time.sleep(15)
        tr_set = b.find_by_tag('tr')
        p = tr_set[id].find_by_tag('a')             # 获取三个点击链接
        p[1].click()
        f = b.find_by_text('付款')                  #找到付款按钮并点击,然后进入付款页面
        f.click()
        p = b.find_by_tag('li')                  # 提取支付选项按钮
        # p[13].click()                           #运动时支付
        p[14].click()                              # 运动经费支付

        # q=b.find_by_text('立即支付')   #最终支付按钮
        # q.click()

#根据给定的时间点和场地对应关系，判断是否满足订场条件，满足则订场，不满足则取消订单
def check_book_or_not(b,already_book_time_set):
    keys=already_book_time_set.keys()   #获取键值
    if len(keys)==0:
        print 'Unfortunately, there is no place for order'
    if len(keys)==1:
        print 'Only one site is reserved'
        pay_for_order(b, already_book_time_set)
        #任选一个场地支付
    if len(keys)==2:
        print 'Congratulations to you! Two time slots are booked.'
        pay_for_order(b, already_book_time_set)
        #任选两个时间段的两个场地支付
    return 0

def print_usage():
    print '=====================================Introduce=========================================='
    print 'Welcome to use the automatic booking software platform of Sun Yat-Sen university gymnasium'
    print 'The input parameters of the platform include your netid name and password, manual input '
    print 'verification code, booking time period, expected field number and number of site ,which '
    print 'can be modified in file conf.cfg.'
    print ''
    print ''
    print '===========================Start reserving badmition site================================'

#读取配置文件信息
def get_message_from_configure_file(filename):
    conf_data={}
    config = ConfigParser.ConfigParser()
    with open(filename,'r') as cfgfile:
        config.readfp(cfgfile)
        conf_data['netid']=config.get('info','netid')
        conf_data['password']=config.get('info','password')
        conf_data['thread_count']=int(config.get('info','thread_count'))
        conf_data['is_delay'] = int(config.get('info', 'is_delay'))

        conf_data['thread_1_site_time'] = config.get('thread1', 'site_time')
        conf_data['thread_1_site_set'] = config.get('thread1', 'site_set').split(',')
        conf_data['thread_1_site_num'] = int(config.get('thread1', 'site_num'))

        conf_data['thread_2_site_time'] = config.get('thread2', 'site_time')
        conf_data['thread_2_site_set'] = config.get('thread2', 'site_set').split(',')
        conf_data['thread_2_site_num'] = int(config.get('thread2', 'site_num'))

    return conf_data

class thread_booking(threading.Thread):
    def __init__(self,b,is_delay,my_time, my_place_num_set,my_place_count):
        threading.Thread.__init__(self)
        self.b=b
        self.my_time=my_time
        self.my_place_num_set=my_place_num_set
        self.my_place_count=my_place_count
        self.is_delay=is_delay

    def run(self):
        if self.is_delay == 1:
            wait_for_booking(self.b)
        start_booking(self.b, self.my_time, self.my_place_num_set, self.my_place_count)

if __name__=='__main__':

    print_usage()
    conf_data=get_message_from_configure_file('config.cfg')
    if conf_data['thread_count'] == 1:
        b1 = login_booking(conf_data['netid'],conf_data['password'])
        if conf_data['is_delay'] == 1:
            wait_for_booking(b1)          #可预订时间的前两天运行
        start_booking(b1, conf_data['thread_1_site_time'], conf_data['thread_1_site_set'],conf_data['thread_1_site_num'])

    elif conf_data['thread_count'] == 2:
        b1 = login_booking(conf_data['netid'],conf_data['password'])
        book_thread_1=thread_booking(b1,conf_data['is_delay'],conf_data['thread_1_site_time'], conf_data['thread_1_site_set'],conf_data['thread_1_site_num'])
        b2 = login_booking(conf_data['netid'],conf_data['password'])
        book_thread_2 = thread_booking(b2,conf_data['is_delay'],conf_data['thread_2_site_time'], conf_data['thread_2_site_set'],conf_data['thread_2_site_num'])

        book_thread_1.setDaemon(True)
        book_thread_1.start()
        book_thread_2.setDaemon(True)
        book_thread_2.start()

        threads=[]

        threads.append(book_thread_1)
        threads.append(book_thread_2)

        for t in threads:
            t.join()

    time.sleep(120)  #延时120秒后开始统计订单预定
    print ''
    print '========================================================================================='
    print 'Start pay for order......'

    already_book_time_set=check_order(b1)
    check_book_or_not(b1,already_book_time_set)
