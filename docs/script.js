document.addEventListener('DOMContentLoaded', () => {
    // 动态导航切换
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    navToggle.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        navToggle.textContent = navLinks.classList.contains('active') ? '✕' : '☰';
    });

    // 星空背景动画
    const canvas = document.getElementById('space-canvas');
    const ctx = canvas.getContext('2d');
    let stars = [];
    
    function initStars() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        stars = [];
        
        for(let i = 0; i < 200; i++) {
            stars.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                radius: Math.random() * 1.5,
                speed: Math.random() * 0.5 + 0.2
            });
        }
    }

    function animateStars() {
        ctx.fillStyle = 'rgba(26, 26, 46, 0.1)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        stars.forEach(star => {
            ctx.beginPath();
            ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(155, 205, 255, ${star.opacity || 0.8})`;
            ctx.fill();

            star.y += star.speed;
            if(star.y > canvas.height) {
                star.y = 0;
                star.x = Math.random() * canvas.width;
            }
        });

        requestAnimationFrame(animateStars);
    }

    // 粒子效果
    class Particle {
        constructor(x, y) {
            this.x = x;
            this.y = y;
            this.size = Math.random() * 5 + 1;
            this.speedX = Math.random() * 3 - 1.5;
            this.speedY = Math.random() * 3 - 1.5;
        }

        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            if(this.size > 0.2) this.size -= 0.1;
        }

        draw() {
            ctx.fillStyle = `rgba(155, 205, 255, ${this.size})`;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    const particles = [];
    canvas.addEventListener('click', (e) => {
        for(let i = 0; i < 5; i++) {
            particles.push(new Particle(e.clientX, e.clientY));
        }
    });

    function handleParticles() {
        for(let i = 0; i < particles.length; i++) {
            particles[i].update();
            particles[i].draw();
            if(particles[i].size <= 0.2) {
                particles.splice(i, 1);
                i--;
            }
        }
    }

    // 初始化
    initStars();
    setInterval(() => {
        if(Math.random() < 0.3) {
            particles.push(new Particle(
                Math.random() * canvas.width,
                Math.random() * canvas.height
            ));
        }
    }, 100);

    // 主循环
    function mainLoop() {
        animateStars();
        handleParticles();
        requestAnimationFrame(mainLoop);
    }

    mainLoop();

    // 窗口调整
    window.addEventListener('resize', () => {
        initStars();
    });
});

