document.addEventListener('DOMContentLoaded', function () {
    // 1. 汉堡菜单点击事件
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', function () {
            navLinks.classList.toggle('active');
            console.log('汉堡菜单被点击，切换 active 类');
        });
    } else {
        console.error('无法找到 .menu-toggle 或 .nav-links 元素');
    }

    // 2. 获取所有的关闭按钮并绑定点击事件
    const closeButtons = document.querySelectorAll('.close-btn');
    console.log(`找到 ${closeButtons.length} 个 .close-btn 元素`);

    closeButtons.forEach(button => {
        button.addEventListener('click', function (event) {
            console.log('关闭按钮被点击');
            event.stopPropagation();
            
            const alertItem = this.parentElement;
            console.log('找到 alertItem:', alertItem);

            if (alertItem) {
                // 添加破碎效果
                alertItem.classList.add('burst');
                console.log('添加 burst 类');

                // 破碎动画结束后移除元素
                alertItem.addEventListener('animationend', function () {
                    alertItem.remove();
                    console.log('移除 alertItem 元素');
                });
            } else {
                console.error('无法找到关闭按钮的父元素');
            }
        });
    });

    // 3. 点击整个 alert 消失效果
    const flashItems = document.querySelectorAll('.flashes li');
    console.log(`找到 ${flashItems.length} 个 .flashes li 元素`);

    flashItems.forEach(item => {
        item.addEventListener('click', function () {
            console.log('flashItem 被点击');
            item.classList.add('burst');
            console.log('添加 burst 类');

            item.addEventListener('animationend', function () {
                item.remove();
                console.log('移除 flashItem 元素');
            });
        });
    });

    // 4. Testimonials Carousel
    const carousel = document.querySelector('.testimonials-carousel'); // 确保类名与HTML匹配
    const testimonials = document.querySelectorAll('.testimonial-item'); // 确保类名与HTML匹配
    let index = 0;

    console.log('找到 .testimonials-carousel 元素:', carousel);
    console.log(`找到 ${testimonials.length} 个 .testimonial-item 元素`);

    if (carousel && testimonials.length > 0) {
        function showNextTestimonial() {
            index = (index + 1) % testimonials.length;
            console.log(`显示下一个 testimonial，索引: ${index}`);
            carousel.style.transform = `translateX(-${index * 100}%)`;
        }

        setInterval(showNextTestimonial, 5000); // 每5秒切换一次评价
    } else {
        console.error('无法找到 .testimonials-carousel 或没有 .testimonial-item 元素');
    }

    // 5. 处理表单提交时的加载状态
    const submitReviewForm = document.getElementById('submitReviewForm');
    const loadingMessage = document.getElementById('loadingMessage');

    if (submitReviewForm && loadingMessage) {
        submitReviewForm.addEventListener('submit', function () {
            loadingMessage.style.display = 'block';
            console.log('表单提交，显示加载消息');
        });
    } else {
        console.error('无法找到 #submitReviewForm 或 #loadingMessage 元素');
    }

    // 6. 点赞功能的 JavaScript 处理
    // 获取 CSRF Token
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    console.log('CSRF Token:', csrfToken);

    const likeButtons = document.querySelectorAll('.like-btn');
    console.log(`找到 ${likeButtons.length} 个 .like-btn 元素`);

    likeButtons.forEach(button => {
        button.addEventListener('click', function () {
            const reviewId = this.getAttribute('data-review-id');
            console.log(`点赞按钮被点击，Review ID: ${reviewId}`);

            fetch(`/reviews/${reviewId}/like`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({}) // 根据后端需求发送数据
            })
            .then(response => response.json())
            .then(data => {
                if (data.likes !== undefined) {
                    this.innerText = `👍 ${data.likes}`;
                    if (data.action === 'liked') {
                        this.classList.add('liked');  // 增加样式以标识已点赞
                        console.log('点赞成功，添加 liked 类');
                    } else {
                        this.classList.remove('liked');  // 移除样式以标识未点赞
                        console.log('取消点赞，移除 liked 类');
                    }
                }
            })
            .catch(error => {
                console.error('点赞请求出错:', error);
            });
        });
    });
});
