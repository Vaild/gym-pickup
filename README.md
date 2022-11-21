主要用于已经知道当前问题答案的情况进行捡漏，目前不支持直接进行预约，因为没有问题的数据库。

- [x] 将Js加密模块改写为Python实现
- [x] 登录模块实现
- [x] 捡漏功能实现

### 使用指南

1. 下载当前项目

````shell
git clone https://github.com/Vaild/gym-pickup.git
````



2. 安装一些必要的包

````
pip install -r requirements.txt
````



3. 主要使用

````shell
cd src
python pickUp.py username password interval buildingcodes
````

`username`: 学号

`password`: 统一校园验证的密码

`interval`: 多少秒刷新一次，**这里不要太快，很有可能会被学校查到**

`buidingcodes`: 要捡漏的场地，可以是多个，用空格隔开

例如：

````
# 捡漏健身房、风雨操场，每30秒查询一次
python pickUp.py 2020XXX passXXXX 30 1001 1003
````

场地号如下：

````json
{
  "健身房": 1001,
  "乒乓球": 1002,
  "风雨操场": 1003,
  "篮球馆": 1004,
  "排球馆": 1005,
  "羽毛球馆": 1006,
  "游泳馆浅水": 1007,
  "游泳馆深水": 1008
}
````



还有一个最主要的操作，就是需要知道每天的问题的答案，并且放到数据库`freshmansno.db`中，这里在`authCodeUtil`模块中已经实现了自动加入到数据中，只需要手动加入答案即可，这里没有那么易用，主要还是因为之前写直接预约程序的时候遗留下来的问题。之后会改到从参数获取问题问题答案。
