"""
DashScope 图片生成 API 诊断脚本
运行命令: cd backend && python -m app.modules.render.tests.test_image_api
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 已加载 .env 文件: {env_path}")
else:
    print(f"⚠️ 未找到 .env 文件: {env_path}")


def test_api_connection():
    """测试 DashScope API 基本连接"""
    print("\n" + "=" * 60)
    print("📡 DashScope 图片生成 API 诊断")
    print("=" * 60)
    
    # 1. 检查 API Key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ 错误: DASHSCOPE_API_KEY 环境变量未设置")
        return False
    
    print(f"✅ API Key: {api_key[:8]}...{api_key[-4:]} (长度: {len(api_key)})")
    
    # 2. 检查 dashscope 库
    try:
        from dashscope import ImageSynthesis
        import dashscope
        print(f"✅ dashscope 库版本: {dashscope.__version__ if hasattr(dashscope, '__version__') else 'unknown'}")
    except ImportError as e:
        print(f"❌ 错误: 无法导入 dashscope 库 - {e}")
        return False
    
    # 3. 测试 API 调用
    print("\n📤 发送测试请求...")
    print(f"   模型: qwen-image-plus")
    print(f"   提示词: '一个红色的苹果，白色背景，简洁风格'")
    print(f"   尺寸: 512*512")
    
    try:
        from http import HTTPStatus
        
        response = ImageSynthesis.call(
            api_key=api_key,
            model="qwen-image-plus",
            prompt="一个红色的苹果，白色背景，简洁风格",
            n=1,
            size="512*512"
        )
        
        print(f"\n📥 API 响应:")
        print(f"   HTTP Status: {response.status_code}")
        print(f"   Code: {response.code}")
        print(f"   Message: {response.message}")
        
        if response.status_code == HTTPStatus.OK:
            print("\n✅ API 调用成功!")
            if response.output and response.output.results:
                image_url = response.output.results[0].url
                print(f"   图片 URL: {image_url[:80]}...")
                return True
            else:
                print("   ⚠️ 返回成功但无图片 URL")
                print(f"   Output: {response.output}")
                return False
        else:
            print(f"\n❌ API 调用失败!")
            print(f"   错误码: {response.code}")
            print(f"   错误信息: {response.message}")
            
            # 常见错误诊断
            if "InvalidApiKey" in str(response.code):
                print("\n💡 诊断: API Key 无效，请检查是否正确复制")
            elif "AccessDenied" in str(response.code):
                print("\n💡 诊断: 访问被拒绝，请检查:")
                print("   1. 是否已开通 qwen-image-plus 模型权限")
                print("   2. 账户是否有足够余额")
            elif "Throttling" in str(response.code):
                print("\n💡 诊断: 请求被限流，请稍后重试")
            elif "InvalidParameter" in str(response.code):
                print("\n💡 诊断: 参数错误，请检查模型名称和参数格式")
            
            return False
            
    except Exception as e:
        print(f"\n❌ 异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_alternative_models():
    """测试其他可用模型"""
    print("\n" + "=" * 60)
    print("🔄 测试其他模型...")
    print("=" * 60)
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return
    
    from dashscope import ImageSynthesis
    from http import HTTPStatus
    
    models_to_test = [
        ("wanx-v1", "512*512"),
        ("wanx2.1-t2i-turbo", "1024*1024"),
    ]
    
    for model, size in models_to_test:
        print(f"\n测试模型: {model}")
        try:
            response = ImageSynthesis.call(
                api_key=api_key,
                model=model,
                prompt="一个红色的苹果",
                n=1,
                size=size
            )
            
            if response.status_code == HTTPStatus.OK:
                print(f"   ✅ {model} 可用")
            else:
                print(f"   ❌ {model}: {response.code} - {response.message}")
        except Exception as e:
            print(f"   ❌ {model}: {e}")


if __name__ == "__main__":
    success = test_api_connection()
    
    if not success:
        print("\n" + "=" * 60)
        print("📋 排查建议:")
        print("=" * 60)
        print("1. 登录百炼控制台: https://bailian.console.aliyun.com/")
        print("2. 检查 '模型服务' -> '模型列表' -> 搜索 'qwen-image'")
        print("3. 确认模型已开通且账户有余额")
        print("4. 如使用子账号，检查 RAM 权限")
        
        # 尝试其他模型
        test_alternative_models()
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
