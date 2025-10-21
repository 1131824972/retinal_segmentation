import pytest
import requests
import base64
import json
import time

# 测试配置
BASE_URL = "http://localhost:8000"
TEST_IMAGE_PATH = "test_image.png"  # 准备一个测试图像文件


def test_health_check():
    """测试健康检查接口"""
    response = requests.get(f"{BASE_URL}/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "retina-segmentation-api" in data["service"]
    assert "timestamp" in data

    print("✅ 健康检查测试通过")


def test_service_info():
    """测试服务信息接口"""
    response = requests.get(f"{BASE_URL}/info")

    assert response.status_code == 200
    data = response.json()

    assert "service_name" in data
    assert "version" in data
    assert "environment" in data

    print("✅ 服务信息测试通过")


def test_model_info():
    """测试模型信息接口"""
    response = requests.get(f"{BASE_URL}/api/v1/model/info")

    assert response.status_code == 200
    data = response.json()

    assert "model_name" in data
    assert "status" in data
    assert "supported_formats" in data

    print("✅ 模型信息测试通过")


def test_base64_prediction():
    """测试Base64预测接口（模拟数据）"""
    # 创建一个小的测试base64数据（1x1像素的PNG）
    test_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    payload = {
        "image_data": f"data:image/png;base64,{test_base64}",
        "image_format": "png"
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/predict",
        json=payload
    )

    # 由于是无效图像，应该返回400错误
    assert response.status_code == 400
    data = response.json()

    assert data["status"] == "error"
    assert "request_id" in data

    print("✅ Base64预测验证测试通过")


def test_system_stats():
    """测试系统统计接口"""
    response = requests.get(f"{BASE_URL}/system/stats")

    # 这个接口可能因为权限问题失败，所以只检查响应格式
    if response.status_code == 200:
        data = response.json()
        assert "cpu_percent" in data or "message" in data
    else:
        # 如果失败，应该返回错误信息
        data = response.json()
        assert "status" in data

    print("✅ 系统统计测试通过")


def run_all_tests():
    """运行所有测试"""
    print("🧪 开始API测试...")

    try:
        test_health_check()
        test_service_info()
        test_model_info()
        test_base64_prediction()
        test_system_stats()

        print("🎉 所有测试通过！")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    # 等待服务启动
    print("⏳ 等待服务启动...")
    time.sleep(2)

    success = run_all_tests()

    if success:
        print("\n📋 测试报告:")
        print("   健康检查: ✅")
        print("   服务信息: ✅")
        print("   模型信息: ✅")
        print("   Base64预测: ✅")
        print("   系统统计: ✅")
        print("\n🚀 API服务测试完成！")
    else:
        print("\n💥 测试失败，请检查服务状态")
        exit(1)