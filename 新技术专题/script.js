// 导航栏滚动效果
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        navbar.classList.add('bg-white/90', 'backdrop-blur-md', 'shadow-md');
        navbar.classList.remove('bg-transparent');
    } else {
        navbar.classList.remove('bg-white/90', 'backdrop-blur-md', 'shadow-md');
        navbar.classList.add('bg-transparent');
    }
});

// 平滑滚动
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            window.scrollTo({
                top: target.offsetTop - 80,
                behavior: 'smooth'
            });
        }
    });
});

// 视差效果
window.addEventListener('scroll', () => {
    // 背景视差效果
    const parallaxBackgrounds = document.querySelectorAll('.parallax-background');
    parallaxBackgrounds.forEach(background => {
        const speed = background.style.getPropertyValue('--parallax-speed') || 0.3;
        const y = window.scrollY * speed;
        background.style.transform = `translateY(${y}px)`;
    });
    
    // 前景元素视差效果
    const parallaxElements = document.querySelectorAll('.parallax-element');
    parallaxElements.forEach(element => {
        const speed = element.style.getPropertyValue('--parallax-speed') || 0.5;
        const y = window.scrollY * speed;
        element.style.transform = `translateY(${y}px)`;
    });
});

// Hero区域加载动画
window.addEventListener('load', () => {
    // 触发Hero区域的动画
    const heroElements = document.querySelectorAll('.hero-animate');
    heroElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        // 使用setTimeout强制重绘
        setTimeout(() => {
            element.classList.add('hero-animate');
        }, 100);
    });
});

// Intersection Observer 动画
const fadeElements = document.querySelectorAll('.fade-in');
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            // 获取元素上的延迟时间
            const delay = entry.target.style.transitionDelay;
            const delayTime = delay ? parseFloat(delay) * 1000 : 0;
            
            // 应用延迟动画
            setTimeout(() => {
                entry.target.classList.add('visible');
                // 对于技术亮点卡片，添加额外的动画效果
                if (entry.target.classList.contains('hover-lift')) {
                    setTimeout(() => {
                        entry.target.style.boxShadow = '0 10px 25px -5px rgba(0, 0, 0, 0.05)';
                    }, 300);
                }
            }, delayTime);
        } else {
            // 当元素离开视口时，移除动画类和阴影，为下次进入视口做准备
            entry.target.classList.remove('visible');
            if (entry.target.classList.contains('hover-lift')) {
                entry.target.style.boxShadow = 'none';
            }
        }
    });
}, {
    threshold: 0.1,
    rootMargin: '0px 0px -10% 0px'
});

fadeElements.forEach(element => {
    observer.observe(element);
});

// 文件上传功能
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeFile = document.getElementById('removeFile');
const processButton = document.getElementById('processButton');
const previewContainer = document.getElementById('previewContainer');
const emptyState = document.getElementById('emptyState');
const singleModelView = document.getElementById('singleModelView');
const compareView = document.getElementById('compareView');
const previewImage = document.getElementById('previewImage');
const baseUnetImage = document.getElementById('baseUnetImage');
const cbamNetImage = document.getElementById('cbamNetImage');
const loadingOverlay = document.getElementById('loadingOverlay');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const originalBtn = document.getElementById('originalBtn');
const segmentedBtn = document.getElementById('segmentedBtn');
const overlayBtn = document.getElementById('overlayBtn');
const modelControls = document.getElementById('modelControls');
const baseUnetBtn = document.getElementById('baseUnetBtn');
const cbamNetBtn = document.getElementById('cbamNetBtn');
const compareBtn = document.getElementById('compareBtn');
const opacitySlider = document.getElementById('opacitySlider');
const opacityValue = document.getElementById('opacityValue');

let selectedFile = null;
let currentView = 'original';
let currentModel = 'baseUnet';
let currentDisplayMode = 'single'; // 'single' 或 'compare'
let originalImageSrc = '';
let segmentedImageSrcBase = '';
let segmentedImageSrcCBAM = '';
let currentOpacity = 50; // 透明度值（10-100）

// 阻止默认拖放行为
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// 高亮拖放区域
['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, unhighlight, false);
});

function highlight() {
    dropZone.classList.add('border-primary');
}

function unhighlight() {
    dropZone.classList.remove('border-primary');
}

// 处理拖放文件
dropZone.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
        handleFiles(files[0]);
    }
}

// 点击上传
dropZone.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        handleFiles(fileInput.files[0]);
    }
});

function handleFiles(file) {
    if (!file.type.match('image.*')) {
        alert('请上传图片文件！');
        return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
        alert('文件大小不能超过5MB！');
        return;
    }

    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    fileInfo.classList.remove('hidden');
    processButton.disabled = false;

    // 预览原图
    const reader = new FileReader();
    reader.onload = (e) => {
        originalImageSrc = e.target.result;
        previewImage.src = originalImageSrc;
        previewImage.style.opacity = '1';
        previewImage.classList.remove('hidden');
        emptyState.classList.add('hidden');
    };
    reader.readAsDataURL(file);
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
    else return (bytes / 1048576).toFixed(2) + ' MB';
}

// 移除文件
removeFile.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    fileInfo.classList.add('hidden');
    processButton.disabled = true;
    singleModelView.classList.add('hidden');
    compareView.classList.add('hidden');
    modelControls.classList.add('hidden');
    emptyState.classList.remove('hidden');
    
    // 重置模型结果和选择状态
    originalImageSrc = '';
    segmentedImageSrcBase = '';
    segmentedImageSrcCBAM = '';
    currentModel = 'baseUnet';
    currentDisplayMode = 'single';
    currentOpacity = 50;
    opacitySlider.value = currentOpacity;
    opacityValue.textContent = `${currentOpacity}%`;
    
    // 重置按钮状态
    baseUnetBtn.classList.add('bg-white', 'text-dark');
    baseUnetBtn.classList.remove('text-dark/70');
    cbamNetBtn.classList.remove('bg-white', 'text-dark');
    cbamNetBtn.classList.add('text-dark/70');
    compareBtn.classList.remove('bg-white', 'text-dark');
    compareBtn.classList.add('text-dark/70');
});

// 处理图像
processButton.addEventListener('click', () => {
    if (!selectedFile) return;

    // 显示加载动画和骨架屏
    loadingOverlay.classList.remove('hidden');
    progressBar.style.width = '0%';
    progressText.textContent = '0%';
    
    // 添加骨架屏效果
    previewContainer.classList.add('animate-pulse');

    // 调用分割处理函数
    processImageSegmentation();
})

// 图像分割处理主函数 - 这里预留了后端API接口
function processImageSegmentation() {
    // 检查是否使用后端API（可配置项）
    const useBackendAPI = false; // 设置为true可使用后端API
    
    if (useBackendAPI) {
        // 后端API调用接口
        callBackendSegmentationAPI();
    } else {
        // 前端模拟处理
        simulateSegmentationProcess();
    }
}

// 后端API调用接口函数
function callBackendSegmentationAPI() {
    // 创建FormData对象，用于发送文件
    const formData = new FormData();
    formData.append('image', selectedFile);
    
    // 配置API端点（这里是预留的接口）
    const apiEndpoint = 'https://api.example.com/segment/vessel';
    
    // 显示加载进度
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += 2;
        progressBar.style.width = `${progress}%`;
    }, 50);
    
    // 发送请求到后端API
    fetch(apiEndpoint, {
        method: 'POST',
        body: formData
        // 如果需要认证，可以添加headers
        // headers: {
        //     'Authorization': 'Bearer YOUR_API_KEY'
        // }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('API请求失败');
        }
        return response.json(); // 假设API返回JSON格式数据
    })
    .then(data => {
        clearInterval(progressInterval);
        progressBar.style.width = '100%';
        
        // 模拟API返回延迟，确保进度条显示完成
        setTimeout(() => {
            loadingOverlay.classList.add('hidden');
            
            // 处理API返回的数据
            // 假设API返回的JSON中包含segmentedImage字段（Base64编码的图像）
            if (data.segmentedImage) {
                segmentedImageSrc = data.segmentedImage;
            } else {
                // 如果API没有返回图像，则使用前端模拟作为备用
                generateSegmentedImage();
            }
            
            updatePreview();
        }, 500);
    })
    .catch(error => {
        clearInterval(progressInterval);
        loadingOverlay.classList.add('hidden');
        console.error('分割API调用失败:', error);
        alert('处理失败，请稍后重试。错误: ' + error.message);
    });
}

// 前端模拟分割处理过程
function simulateSegmentationProcess() {
    // 模拟处理进度
    let progress = 0;
    const interval = setInterval(() => {
        progress += 5;
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `${progress}%`;
        
        if (progress >= 100) {
            clearInterval(interval);
            // 模拟处理完成
            setTimeout(() => {
                loadingOverlay.classList.add('hidden');
                previewContainer.classList.remove('animate-pulse');
                
                // 生成两个模型的分割图像
                generateSegmentedImage('baseUnet');
                setTimeout(() => {
                    generateSegmentedImage('cbamNet');
                    
                    // 显示模型控制和预览
                    modelControls.classList.remove('hidden');
                    updatePreview();
                }, 300);
            }, 500);
        }
    }, 100);
}

// 切换预览模式
originalBtn.addEventListener('click', () => {
    currentView = 'original';
    updatePreviewButtons();
    updatePreview();
});

segmentedBtn.addEventListener('click', () => {
    currentView = 'segmented';
    updatePreviewButtons();
    updatePreview();
});

overlayBtn.addEventListener('click', () => {
    currentView = 'overlay';
    updatePreviewButtons();
    updatePreview();
});

// 模型选择按钮事件监听
baseUnetBtn.addEventListener('click', () => {
    currentModel = 'baseUnet';
    currentDisplayMode = 'single';
    updateModelButtons();
    updatePreview();
});

cbamNetBtn.addEventListener('click', () => {
    currentModel = 'cbamNet';
    currentDisplayMode = 'single';
    updateModelButtons();
    updatePreview();
});

compareBtn.addEventListener('click', () => {
    currentDisplayMode = 'compare';
    updateModelButtons();
    updatePreview();
});

// 透明度滑块事件监听
opacitySlider.addEventListener('input', () => {
    currentOpacity = parseInt(opacitySlider.value);
    opacityValue.textContent = `${currentOpacity}%`;
    
    // 当当前视图是叠加图时，更新预览
    if (currentView === 'overlay') {
        updatePreview();
    }
});

// 更新预览模式按钮
function updatePreviewButtons() {
    originalBtn.classList.toggle('bg-primary', currentView === 'original');
    originalBtn.classList.toggle('text-white', currentView === 'original');
    originalBtn.classList.toggle('text-dark/70', currentView !== 'original');
    
    segmentedBtn.classList.toggle('bg-primary', currentView === 'segmented');
    segmentedBtn.classList.toggle('text-white', currentView === 'segmented');
    segmentedBtn.classList.toggle('text-dark/70', currentView !== 'segmented');
    
    overlayBtn.classList.toggle('bg-primary', currentView === 'overlay');
    overlayBtn.classList.toggle('text-white', currentView === 'overlay');
    overlayBtn.classList.toggle('text-dark/70', currentView !== 'overlay');
}

// 更新模型选择按钮
function updateModelButtons() {
    // 重置所有按钮
    baseUnetBtn.classList.remove('bg-white', 'text-dark');
    baseUnetBtn.classList.add('text-dark/70');
    cbamNetBtn.classList.remove('bg-white', 'text-dark');
    cbamNetBtn.classList.add('text-dark/70');
    compareBtn.classList.remove('bg-white', 'text-dark');
    compareBtn.classList.add('text-dark/70');
    
    // 更新当前选中的按钮
    if (currentDisplayMode === 'single') {
        if (currentModel === 'baseUnet') {
            baseUnetBtn.classList.add('bg-white', 'text-dark');
            baseUnetBtn.classList.remove('text-dark/70');
        } else {
            cbamNetBtn.classList.add('bg-white', 'text-dark');
            cbamNetBtn.classList.remove('text-dark/70');
        }
    } else {
        compareBtn.classList.add('bg-white', 'text-dark');
        compareBtn.classList.remove('text-dark/70');
    }
}

// 更新预览
function updatePreview() {
    // 显示预览区域，隐藏空状态
    emptyState.classList.add('hidden');
    
    if (currentDisplayMode === 'single') {
        // 显示单模型预览，隐藏对比预览
        singleModelView.classList.remove('hidden');
        compareView.classList.add('hidden');
        
        // 根据当前视图模式更新预览
        if (currentView === 'original') {
            previewImage.src = originalImageSrc;
            previewImage.style.opacity = '1';
        } else if (currentView === 'segmented') {
            const currentModelSrc = currentModel === 'baseUnet' ? segmentedImageSrcBase : segmentedImageSrcCBAM;
            previewImage.src = currentModelSrc;
            previewImage.style.opacity = '1';
        } else if (currentView === 'overlay') {
            // 创建叠加效果
            createOverlayImage();
        }
    } else {
        // 显示对比预览，隐藏单模型预览
        singleModelView.classList.add('hidden');
        compareView.classList.remove('hidden');
        
        // 设置对比视图中的图像
        if (currentView === 'original') {
            baseUnetImage.src = originalImageSrc;
            cbamNetImage.src = originalImageSrc;
        } else if (currentView === 'segmented') {
            baseUnetImage.src = segmentedImageSrcBase;
            cbamNetImage.src = segmentedImageSrcCBAM;
        } else if (currentView === 'overlay') {
            // 为每个模型创建叠加图
            createOverlayImageForComparison();
        }
    }
}

// 生成模拟的分割图像
function generateSegmentedImage(modelType) {
    // 创建一个canvas用于处理图像
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = function() {
        // 设置canvas尺寸
        canvas.width = img.width;
        canvas.height = img.height;
        
        // 绘制原始图像
        ctx.drawImage(img, 0, 0);
        
        // 获取图像数据
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        
        // 根据模型类型设置不同的阈值和颜色
        const threshold = modelType === 'cbamNet' ? 90 : 100;
        const vesselColor = modelType === 'cbamNet' ? [0, 0, 255] : [255, 0, 0]; // CBAM-Net使用蓝色，BaseU-Net使用红色
        
        // 模拟血管分割效果（简单的边缘检测和阈值处理）
        for (let i = 0; i < data.length; i += 4) {
            // 提取灰度值
            const gray = 0.2989 * data[i] + 0.5870 * data[i+1] + 0.1140 * data[i+2];
            
            // 简单的阈值分割 - 假设血管在图像中是相对较暗的部分
            if (gray < threshold) {
                // 显示为对应颜色的血管
                data[i] = vesselColor[0];     // Red
                data[i+1] = vesselColor[1];   // Green
                data[i+2] = vesselColor[2];   // Blue
                data[i+3] = 255;             // Alpha
            } else {
                // 背景变为白色
                data[i] = 255;
                data[i+1] = 255;
                data[i+2] = 255;
                data[i+3] = 255;
            }
        }
        
        // 把处理后的数据放回canvas
        ctx.putImageData(imageData, 0, 0);
        
        // 保存分割后的图像
        if (modelType === 'baseUnet') {
            segmentedImageSrcBase = canvas.toDataURL('image/png');
        } else {
            segmentedImageSrcCBAM = canvas.toDataURL('image/png');
        }
    };
    
    // 设置图像源
    img.src = originalImageSrc;
}

// 创建叠加效果图像（单模型）
function createOverlayImage() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const originalImg = new Image();
    const segmentedImg = new Image();
    
    // 选择当前模型的分割结果
    const currentModelSrc = currentModel === 'baseUnet' ? segmentedImageSrcBase : segmentedImageSrcCBAM;
    
    // 加载分割图像
    segmentedImg.onload = function() {
        // 设置canvas尺寸
        canvas.width = originalImg.width;
        canvas.height = originalImg.height;
        
        // 绘制原始图像
        ctx.drawImage(originalImg, 0, 0);
        
        // 设置全局透明度，然后绘制分割图像
        ctx.globalAlpha = currentOpacity / 100;
        ctx.drawImage(segmentedImg, 0, 0);
        ctx.globalAlpha = 1.0;
        
        // 更新预览图像
        previewImage.src = canvas.toDataURL('image/png');
        previewImage.style.opacity = '1';
    };
    
    // 加载原始图像
    originalImg.onload = function() {
        // 开始加载分割图像
        segmentedImg.src = currentModelSrc;
    };
    
    // 设置原始图像源
    originalImg.src = originalImageSrc;
}

// 创建叠加效果图像（对比视图）
function createOverlayImageForComparison() {
    // 为BaseU-Net创建叠加图
    const baseUnetCanvas = document.createElement('canvas');
    const baseUnetCtx = baseUnetCanvas.getContext('2d');
    const originalImg1 = new Image();
    const segmentedImg1 = new Image();
    
    // 为CBAM-Net创建叠加图
    const cbamNetCanvas = document.createElement('canvas');
    const cbamNetCtx = cbamNetCanvas.getContext('2d');
    const originalImg2 = new Image();
    const segmentedImg2 = new Image();
    
    // 加载BaseU-Net的分割图像
    segmentedImg1.onload = function() {
        // 设置canvas尺寸
        baseUnetCanvas.width = originalImg1.width;
        baseUnetCanvas.height = originalImg1.height;
        
        // 绘制原始图像
        baseUnetCtx.drawImage(originalImg1, 0, 0);
        
        // 设置全局透明度，然后绘制分割图像
        baseUnetCtx.globalAlpha = currentOpacity / 100;
        baseUnetCtx.drawImage(segmentedImg1, 0, 0);
        baseUnetCtx.globalAlpha = 1.0;
        
        // 更新BaseU-Net预览图像
        baseUnetImage.src = baseUnetCanvas.toDataURL('image/png');
    };
    
    // 加载CBAM-Net的分割图像
    segmentedImg2.onload = function() {
        // 设置canvas尺寸
        cbamNetCanvas.width = originalImg2.width;
        cbamNetCanvas.height = originalImg2.height;
        
        // 绘制原始图像
        cbamNetCtx.drawImage(originalImg2, 0, 0);
        
        // 设置全局透明度，然后绘制分割图像
        cbamNetCtx.globalAlpha = currentOpacity / 100;
        cbamNetCtx.drawImage(segmentedImg2, 0, 0);
        cbamNetCtx.globalAlpha = 1.0;
        
        // 更新CBAM-Net预览图像
        cbamNetImage.src = cbamNetCanvas.toDataURL('image/png');
    };
    
    // 加载原始图像
    originalImg1.onload = function() {
        segmentedImg1.src = segmentedImageSrcBase;
    };
    
    originalImg2.onload = function() {
        segmentedImg2.src = segmentedImageSrcCBAM;
    };
    
    // 设置原始图像源
    originalImg1.src = originalImageSrc;
    originalImg2.src = originalImageSrc;
}

// 初始化 ECharts
function initCharts() {
    // 自定义图表主题颜色
    const chartColors = {
        primary: '#0071e3',
        secondary: '#34aadc',
        accent: '#5856d6',
        gray: '#8e8e93'
    };
    
    // 图表通用配置
    const commonOptions = {
        animation: true,
        animationDuration: 1500,
        animationEasing: 'cubicOut',
        animationDelay: function(idx) {
            return idx * 100;
        }
    };

    // 准确率对比图
    const accuracyChart = echarts.init(document.getElementById('accuracyChart'));
    accuracyChart.setOption({
        ...commonOptions,
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow',
                shadowStyle: {
                    color: 'rgba(0, 113, 227, 0.1)'
                }
            },
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#e0e0e0',
            borderWidth: 1,
            textStyle: {
                color: '#333'
            },
            formatter: function(params) {
                return params[0].name + '<br/>' + 
                       params[0].seriesName + ': ' + 
                       (params[0].value * 100).toFixed(1) + '%';
            }
        },
        legend: {
            data: ['准确率'],
            top: 10
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            top: '15%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: ['传统U-Net', 'ResNet+U-Net', 'Transformer+U-Net', '我们的方法'],
            axisLabel: {
                rotate: 30,
                color: '#666',
                fontSize: 12
            },
            axisLine: {
                lineStyle: {
                    color: '#e0e0e0'
                }
            },
            axisTick: {
                alignWithLabel: true
            }
        },
        yAxis: {
            type: 'value',
            min: 0.8,
            max: 1,
            axisLabel: {
                color: '#666',
                fontSize: 12,
                formatter: function(value) {
                    return (value * 100).toFixed(0) + '%';
                }
            },
            splitLine: {
                lineStyle: {
                    color: '#f0f0f0',
                    type: 'dashed'
                }
            }
        },
        series: [{
            name: '准确率',
            type: 'bar',
            data: [0.85, 0.89, 0.92, 0.96],
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: chartColors.primary },
                    { offset: 1, color: chartColors.secondary }
                ]),
                borderRadius: [6, 6, 0, 0]
            },
            barWidth: '40%',
            emphasis: {
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: chartColors.secondary },
                        { offset: 1, color: chartColors.accent }
                    ])
                },
                scale: true,
                scaleSize: 5
            },
            // 添加数字标签
            label: {
                show: true,
                position: 'top',
                formatter: function(params) {
                    return (params.value * 100).toFixed(1) + '%';
                },
                color: chartColors.primary,
                fontSize: 12,
                fontWeight: 'bold'
            }
        }]
    });

    // 血管尺寸分布图
    const vesselSizeChart = echarts.init(document.getElementById('vesselSizeChart'));
    vesselSizeChart.setOption({
        ...commonOptions,
        tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#e0e0e0',
            borderWidth: 1,
            textStyle: {
                color: '#333'
            },
            formatter: function(params) {
                return params.name + '<br/>' + 
                       '比例: ' + params.value + '%<br/>' +
                       '分割准确率: ' + 
                       (params.name === '大血管' ? '98.5%' : 
                        params.name === '中血管' ? '96.2%' : '94.8%');
            }
        },
        legend: {
            top: 'bottom',
            left: 'center',
            textStyle: {
                color: '#666',
                fontSize: 12
            }
        },
        series: [{
            name: '血管尺寸',
            type: 'pie',
            radius: ['45%', '70%'],
            center: ['50%', '45%'],
            avoidLabelOverlap: false,
            itemStyle: {
                borderRadius: 10,
                borderColor: '#fff',
                borderWidth: 3,
                shadowBlur: 5,
                shadowColor: 'rgba(0, 0, 0, 0.1)'
            },
            label: {
                show: false,
                position: 'center'
            },
            emphasis: {
                scale: true,
                scaleSize: 5,
                label: {
                    show: true,
                    fontSize: '20',
                    fontWeight: 'bold',
                    formatter: function(params) {
                        return params.name + '\n' + params.value + '%';
                    }
                },
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.2)'
                }
            },
            labelLine: {
                show: false
            },
            data: [
                { value: 35, name: '大血管', itemStyle: { color: chartColors.primary } },
                { value: 25, name: '中血管', itemStyle: { color: chartColors.secondary } },
                { value: 40, name: '小血管', itemStyle: { color: chartColors.accent } }
            ]
        }]
    });

    // 性能指标雷达图
    const performanceChart = echarts.init(document.getElementById('performanceChart'));
    performanceChart.setOption({
        ...commonOptions,
        tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#e0e0e0',
            borderWidth: 1,
            textStyle: {
                color: '#333'
            }
        },
        legend: {
            data: ['我们的方法', '其他方法'],
            bottom: 10,
            textStyle: {
                color: '#666',
                fontSize: 12
            }
        },
        radar: {
            indicator: [
                { name: 'DSC系数', max: 1 },
                { name: 'Hausdorff距离', max: 1 },
                { name: '敏感度', max: 1 },
                { name: '特异度', max: 1 },
                { name: '准确率', max: 1 },
                { name: '处理速度', max: 1 }
            ],
            shape: 'circle',
            splitNumber: 5,
            axisName: {
                color: '#666',
                fontSize: 12
            },
            splitLine: {
                lineStyle: {
                    color: ['rgba(0, 113, 227, 0.1)', 'rgba(0, 113, 227, 0.2)', 
                            'rgba(0, 113, 227, 0.3)', 'rgba(0, 113, 227, 0.4)', 
                            'rgba(0, 113, 227, 0.5)'].reverse()
                }
            },
            splitArea: {
                show: false
            },
            axisLine: {
                lineStyle: {
                    color: 'rgba(0, 113, 227, 0.5)'
                }
            }
        },
        series: [{
            name: '性能指标',
            type: 'radar',
            data: [
                {
                    value: [0.96, 0.93, 0.95, 0.94, 0.96, 0.88],
                    name: '我们的方法',
                    symbol: 'circle',
                    symbolSize: 6,
                    itemStyle: { color: chartColors.primary },
                    lineStyle: {
                        color: chartColors.primary,
                        width: 2
                    },
                    areaStyle: {
                        color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                            { offset: 0, color: 'rgba(0, 113, 227, 0.8)' },
                            { offset: 1, color: 'rgba(0, 113, 227, 0.2)' }
                        ])
                    },
                    emphasis: {
                        scale: true,
                        scaleSize: 8,
                        itemStyle: {
                            color: chartColors.primary,
                            borderWidth: 2,
                            borderColor: '#fff'
                        }
                    }
                },
                {
                    value: [0.90, 0.85, 0.88, 0.90, 0.92, 0.85],
                    name: '其他方法',
                    symbol: 'circle',
                    symbolSize: 6,
                    itemStyle: { color: chartColors.gray },
                    lineStyle: {
                        color: chartColors.gray,
                        width: 2
                    },
                    areaStyle: {
                        color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                            { offset: 0, color: 'rgba(142, 142, 147, 0.6)' },
                            { offset: 1, color: 'rgba(142, 142, 147, 0.1)' }
                        ])
                    }
                }
            ]
        }]
    });

    // 添加图表进入视口时的动画触发
    const chartObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // 触发图表重绘以展示动画
                accuracyChart.resize();
                vesselSizeChart.resize();
                performanceChart.resize();
                chartObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });

    // 观察容器元素
    if (document.getElementById('visualization')) {
        chartObserver.observe(document.getElementById('visualization'));
    }

    // 窗口调整时重新渲染图表
    window.addEventListener('resize', () => {
        accuracyChart.resize();
        vesselSizeChart.resize();
        performanceChart.resize();
    });
}

// 页面加载完成后初始化图表
window.addEventListener('DOMContentLoaded', () => {
    // 延迟初始化图表，确保页面完全加载
    setTimeout(() => {
        initCharts();
    }, 1000);
});