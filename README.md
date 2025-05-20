# ha-xiaozhi-mcp
homeassistant mcpserver的临时中转方案

下载全部文件到你的环境中

1.安装依赖

  执行 pip install -r requirements.txt
  
2.配置conf

  api_key ha的长效token
  
  base_url ha的地址，在本地环境就填局域网地址
  
  MCP_ENDPOINT 小智官方提供的mcp地址

  
3.启动mcpserver

  执行 python mcp_pipe.py hass.py

4.检查状态

运行成功后检查mcp配置里是否正常显示三个可用工具

![image](https://github.com/user-attachments/assets/0094b793-3e5d-4dd2-b7ea-0db48c5aa65e)


5.配置提示词

在小智的提示词里加入你的设备信息，之前在三方server有部署过的可以直接粘贴，没整理过得可以用我这个模板去批量获取一下
（尽量精简，不要贴太多无用的传感器）
我的例子：

×××你的其他提示词×××
你也可以帮我控制家里的智能设备，你所在的位置在书房，未指定区域的情况下优先控制书房的设备。你的以下是设备列表：
- 房间,设备名称,设备id(entity_id)
- 书房,吸顶灯,light.649e3159aa36_light
- 书房,音响,media_player.shu_fang_2
- 书房,显示器挂灯,light.yeelink_lamp22_fd36_light
- 书房,灯带,light.plug_158df955a6167a


批量获取设备的模板：
{% set area_list=['书房','主卧'] %}
{% for area in area_list %}
{% set device_list = area_entities(area) | reject('is_hidden_entity') %}
{% for device in device_list %}
{% if 'light' in device or 'switch' in device %}
{{area}},{{device}},{{state_attr(device, 'friendly_name')}}
{% endif %}
{% endfor%}
{% endfor%}
