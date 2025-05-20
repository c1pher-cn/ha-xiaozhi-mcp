from mcp.server.fastmcp import FastMCP
import logging
import requests
from typing import Dict, Any, Literal, Optional, List
from pydantic import BaseModel, Field, validator
from conf import HASS_CONFIG

# 初始化日志
logger = logging.getLogger('hass_device_query')

# 创建 MCP 服务器
mcp = FastMCP("HomeAssistantDeviceQuery")





@mcp.tool()
def hass_play_music(entity_id: str, media_content_id: str = "random") -> Dict[str, Any]:
    """
    在指定媒体播放器上播放音乐或有声书

    Args:
        entity_id: 媒体播放器的entity_id (如 "media_player.living_room_speaker")
        media_content_id: 音乐/有声书 (专辑名/歌曲名/艺术家中英文都可以或 "random")

    Returns:
        包含操作结果的字典
    已知设备:
    书房,音响,media_player.shu_fang_2
   """
    url = f"{HASS_CONFIG['base_url']}/api/services/music_assistant/play_media"
    headers = {
        "Authorization": f"Bearer {HASS_CONFIG['api_key']}",
        "Content-Type": "application/json"
    }
    payload = {
        "entity_id": entity_id,
        "media_id": media_content_id
    }

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        if response.status_code == 200:
            result = {
                "success": True,
                "message": f"正在 {entity_id} 播放: {media_content_id}",
                "response": response.json()
            }
            logger.info(f"播放成功 - 设备: {entity_id}, 内容: {media_content_id}")
            return result
        else:
            error_msg = f"播放失败,entity_id:{entity_id},media_content_id:{media_content_id}，状态码: {response.status_code}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "details": response.text
            }
    except Exception as e:
        error_msg = f"播放异常: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


@mcp.tool()
def hass_get_state(entity_id: str) -> Dict[str, Any]:
    """
    查询 Home Assistant 中设备的状态，包括灯光亮度、颜色、色温，媒体播放器的音量等。

    Args:
        entity_id: Home Assistant 中的设备 entity_id (例如 "light.living_room")

    Returns:
        包含设备状态和属性的字典，或错误信息
    """
    url = f"{HASS_CONFIG['base_url']}/api/states/{entity_id}"
    headers = {
        "Authorization": f"Bearer {HASS_CONFIG['api_key']}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            responsetext = '设备状态:' + response.json()['state'] + ' '

            if 'media_title' in response.json()['attributes']:
                responsetext = responsetext+ '正在播放的是:'+str(response.json()['attributes']['media_title'])+' '
            if 'volume_level' in response.json()['attributes']:
                responsetext = responsetext+ '音量是:'+str(response.json()['attributes']['volume_level'])+' '
            if 'color_temp_kelvin' in response.json()['attributes']:
                responsetext = responsetext+ '色温是:'+str(response.json()['attributes']['color_temp_kelvin'])+' '
            if 'rgb_color' in response.json()['attributes']:
                responsetext = responsetext+ 'rgb颜色是:'+str(response.json()['attributes']['rgb_color'])+' '
            if response.json()['attributes'].get('brightness') is not None:
                brightness_pct = round(( response.json()['attributes']['brightness'] / 255) * 100)
                responsetext += f"亮度是: {brightness_pct}% "
                #responsetext = responsetext+ '亮度是:'+str(response.json()['attributes']['brightness']/255)+' '

            # 构造响应结果
            result = {
                "success": True,
                "state":response.json()['state'],
                "attributes": responsetext
            }
            logger.info(f"查询成功 - 设备: {entity_id}, 状态: {responsetext}")
            return result
        else:
            error_msg = f"查询失败，状态码: {response.status_code}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"查询异常: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

class HassTargetModel(BaseModel):
    """智能家居设备操作目标参数模型"""
    type: Literal[
        'turn_on', 'turn_off',
        'brightness_up', 'brightness_down', 'brightness_value',
        'volume_up', 'volume_down', 'volume_set','set_temperature',
        'set_kelvin', 'set_color',
        'pause', 'continue', 'volume_mute'
    ] = Field(..., description="操作类型对应：打开设备:turn_on,关闭设备:turn_off,增加亮度:brightness_up,降低亮度:brightness_down,设置亮度:brightness_value,增加音量:volume_up,降低音>量:volume_down,设置音量:volume_set,设置温度:set_temperature,设置色温:set_kelvin,设置颜色:set_color,设备暂停:pause,设备继续:continue,静音/取消静音:volume_mute")

    input: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="设置值(0-100)，仅在brightness_value/volume_set时需要"
    )
    input: Optional[int] = Field(
        None,
        ge=17,
        le=30,
        description="设置值(17-30)，仅在set_temperature时需要"
    )

    is_muted: Optional[bool] = Field(
        None,
        description="静音状态True/False，仅在volume_mute时需要"
    )

    rgb_color: Optional[List[int]] = Field(
        None,
        min_items=3,
        max_items=3,
        description="RGB颜色值，仅在set_color时需要"
    )

    @validator('rgb_color')
    def validate_rgb(cls, v):
        if v is not None:
            if any(c < 0 or c > 255 for c in v):
                raise ValueError("RGB值必须在0-255范围内")
        return v

@mcp.tool()
def hass_set_state(entity_id: str, target: HassTargetModel) -> Dict[str, Any]:
    """
    设置智能家居设备状态

    Args:
        entity_id: 设备ID (如: light.bedroom, media_player.living_room)
        target: 操作目标参数，使用 HassTargetModel 验证

    Returns:
        Dict[str, Any]: 操作结果，包含状态和可能的错误信息

    Example:
    >>> # 设置灯光亮度为50%
    >>> hass_set_state(
    ...     entity_id="light.bedroom",
    ...     target={"type": "brightness_value", "input": 50}
    ... )
    >>>
    >>> # 设置RGB颜色
    >>> hass_set_state(
    ...     entity_id="light.kitchen",
    ...     target={"type": "set_color", "rgb_color": [255, 100, 0]}
    ... )
    >>> # 设置空调温度
    >>> hass_set_state(
    ...     entity_id="climate.ac",
    ...     target={"type": "set_temperature", "input": 26}
    ... )
    """
    # 执行操作
    try:
        logger.info(f"状态设置 - 设备: {entity_id}, target:{target.dict()}")
        # 提取设备域 (如 "light" from "light.bedroom")
        domain = entity_id.split(".")[0] if "." in entity_id else None
        if not domain:
            return {"success": False, "error": "无效的entity_id格式"}
        # 将Pydantic模型转换为字典以便处理器使用
        target_dict = target.dict()
        # 解析操作类型
        action_map = {
            "turn_on": _handle_turn_on,
            "turn_off": _handle_turn_off,
            "brightness_up": _handle_brightness_up,
            "brightness_down": _handle_brightness_down,
            "brightness_value": _handle_brightness_value,
            "set_temperature": _handle_set_temperature_value,
            "set_color": _handle_set_color,
            "set_kelvin": _handle_set_kelvin,
            "volume_up": _handle_volume_up,
            "volume_down": _handle_volume_down,
            "volume_set": _handle_volume_set,
            "volume_mute": _handle_volume_mute,
            "pause": _handle_pause,
            "continue": _handle_continue
        }

        handler = action_map.get(target.type)
        if not handler:
            return {"success": False, "error": f"不支持的操作类型: {target.type}"}
        logger.info(f"进入 handler")
        result = handler(domain, entity_id, target_dict)
        logger.info(f"控制成功 - 设备: {entity_id}, 操作: {target.type}")
        return {"success": True, "message": result["description"]}
    except Exception as e:
        error_msg = f"控制失败: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


# --- 操作处理器 ---
def _handle_turn_on(domain: str, entity_id: str, state: Dict) -> Dict:
    """处理打开操作"""
    action = {
        "cover": "open_cover",
        "vacuum": "start"
    }.get(domain, "turn_on")
    logger.info(f"处理函数- 设备: {entity_id}, action:{action}, domain:{domain}, state:{state}")
    return _call_service(domain, action, entity_id, description="设备已打开")

def _handle_turn_off(domain: str, entity_id: str, state: Dict) -> Dict:
    """处理关闭操作"""
    action = {
        "cover": "close_cover",
        "vacuum": "stop"
    }.get(domain, "turn_off")
    logger.info(f"处理函数- 设备: {entity_id}, action:{action}, domain:{domain}, state:{state}")
    return _call_service(domain, action, entity_id, description="设备已关闭")

def _handle_brightness_up(domain: str, entity_id: str, state: Dict) -> Dict:
    """调高亮度"""
    return _call_service(
        domain, "turn_on", entity_id,
        params={"brightness_step_pct": 10},
        description="亮度已调高"
    )

def _handle_brightness_down(domain: str, entity_id: str, state: Dict) -> Dict:
    """调低亮度"""
    return _call_service(
        domain, "turn_on", entity_id,
        params={"brightness_step_pct": -10},
        description="亮度已调低"
    )
def _handle_set_temperature_value(domain: str, entity_id: str, state: Dict) -> Dict:
    """设置温度值"""
    return _call_service(
        domain, "set_temperature", entity_id,
        params={"temperature": state["input"]},
        description=f"温度已设置为{state['input']}%"
    )
def _handle_brightness_value(domain: str, entity_id: str, state: Dict) -> Dict:
    """设置亮度值"""
    return _call_service(
        domain, "turn_on", entity_id,
        params={"brightness_pct": state["input"]},
        description=f"亮度已设置为{state['input']}%"
    )

def _handle_set_color(domain: str, entity_id: str, state: Dict) -> Dict:
    """设置颜色"""
    return _call_service(
        domain, "turn_on", entity_id,
        params={"rgb_color": state["rgb_color"]},
        description=f"颜色已设置为{state['rgb_color']}"
    )

def _handle_set_kelvin(domain: str, entity_id: str, state: Dict) -> Dict:
    """设置色温"""
    return _call_service(
        domain, "turn_on", entity_id,
        params={"kelvin": state["input"]},
        description=f"色温已设置为{state['input']}K"
    )

def _handle_volume_up(domain: str, entity_id: str, state: Dict) -> Dict:
    """音量增加"""
    return _call_service(
        domain, "volume_up", entity_id,
        description="音量已调高"
    )

def _handle_volume_down(domain: str, entity_id: str, state: Dict) -> Dict:
    """音量降低"""
    return _call_service(
        domain, "volume_down", entity_id,
        description="音量已调低"
    )

def _handle_volume_set(domain: str, entity_id: str, state: Dict) -> Dict:
    """设置音量"""
    volume = state["input"] / 100  # 转换为0-1范围
    return _call_service(
        domain, "volume_set", entity_id,
        params={"volume_level": volume},
        description=f"音量已设置为{state['input']}%"
    )

def _handle_volume_mute(domain: str, entity_id: str, state: Dict) -> Dict:
    """静音/取消静音"""
    return _call_service(
        domain, "volume_mute", entity_id,
        params={"is_volume_muted": state["is_muted"].lower() == "true"},
        description="已静音" if state["is_muted"] else "已取消静音"
    )

def _handle_pause(domain: str, entity_id: str, state: Dict) -> Dict:
    """暂停"""
    action = {
        "media_player": "media_pause",
        "cover": "stop_cover",
        "vacuum": "pause"
    }.get(domain, "pause")
    return _call_service(domain, action, entity_id, description="设备已暂停")

def _handle_continue(domain: str, entity_id: str, state: Dict) -> Dict:
    """继续"""
    action = {
        "media_player": "media_play",
        "vacuum": "start"
    }.get(domain, "continue")

    return _call_service(domain, action, entity_id, description="设备已继续")


# --- 通用服务调用 ---
def _call_service(
    domain: str,
    service: str,
    entity_id: str,
    params: Dict = None,
    description: str = ""
) -> Dict:

    logger.info(f"处理函数- 设备: {entity_id}, service:{service}, domain:{domain}, params:{params}")

    """调用Home Assistant服务"""
    url = f"{HASS_CONFIG['base_url']}/api/services/{domain}/{service}"
    headers = {
        "Authorization": f"Bearer {HASS_CONFIG['api_key']}",
        "Content-Type": "application/json"
    }
    data = {"entity_id": entity_id, **(params or {})}


    response = requests.post(url, headers=headers, json=data, verify=False)
    if response.status_code != 200:
        raise Exception(f"API返回错误: {response.status_code} - {response.text}")

    return {"description": description}


# 启动服务器
if __name__ == "__main__":
    mcp.run(transport="stdio")



