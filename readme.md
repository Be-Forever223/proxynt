# 内网穿透工具


## 原理
![原理](./image.png)

## 特性

1. 公网和内网机器之间通信使用 WebSocket
2. 跨平台. 工具用到的 Python 第三方库有: tornado, websocket-client, typing_extensions

## 使用前

安装依赖

```
pip install -r requirements.txt
```

## 使用

客户端
```
python run_client.py -c config_c.json
```

服务端
```
python run_server.py -c config_s.json
```

服务端ui: 
```
管理页面路径为websocket路径+admin,
比如 
http://192.168.9.229:18888/websocketpath1/admin
```

![原理](./ui.png)

## 示例, 通过 SSH 访问内网机器

假设公网机器的ip是 `192.168.9.224`

#### 1. 在公网机器上配置`config_s.json`, 设置连接密码, 接受客户端配置的端口和websocket路径
```json
{
  "port": 18888,
  "password": "helloworld",
  "path": "/websocket_path"
}
```
然后启动: 
`python run_server.py -c config_s.json `

#### 2. 在需要被访问的内网电脑上配置`config_c.json`
 配置config_c.json
 
```json
{
  "server": {
    "port": 18888,
    "host": "192.168.9.224",
    "https": false,
    "password": "helloworld",
    "path": "/websocket_path"
  },
  "client": [
    {
      "name": "ssh1",
      "remote_port": 12222,
      "local_port": 22,
      "local_ip": "127.0.0.1"
    }
  ]
}
```

然后启动: 
`python run_client.py -c config_c.json`

#### 3. ssh 连接: 
```
ssh -oPort=12222 test@192.168.9.224
```


#### 打开管理页面:

```
http://192.168.9.224:18888/websocketpath/admin
```
