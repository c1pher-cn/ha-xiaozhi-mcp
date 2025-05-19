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
