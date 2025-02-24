// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 自动隐藏闪现消息
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 3000);
    });
}); 