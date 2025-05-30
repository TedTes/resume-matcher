// Main JavaScript for Resume Matcher

document.addEventListener('DOMContentLoaded', function() {
    // Mobile Navigation Toggle
    const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileNavToggle && navLinks) {
        mobileNavToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
            document.body.classList.toggle('nav-open');
            
            // Transform hamburger to X
            this.classList.toggle('active');
        });
        
        // Close mobile nav when clicking outside
        document.addEventListener('click', function(event) {
            if (!event.target.closest('.mobile-nav-toggle') && 
                !event.target.closest('.nav-links') && 
                navLinks.classList.contains('active')) {
                navLinks.classList.remove('active');
                document.body.classList.remove('nav-open');
                mobileNavToggle.classList.remove('active');
            }
        });
        
        // Close mobile nav when clicking on a link
        const navItems = navLinks.querySelectorAll('a');
        navItems.forEach(item => {
            item.addEventListener('click', function() {
                navLinks.classList.remove('active');
                document.body.classList.remove('nav-open');
                mobileNavToggle.classList.remove('active');
            });
        });
    }
    
    // Sticky Navigation
    const mainNav = document.querySelector('.main-nav');
    
    if (mainNav) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 100) {
                mainNav.classList.add('scrolled');
            } else {
                mainNav.classList.remove('scrolled');
            }
        });
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const hrefValue = this.getAttribute('href');
        
            // Skip empty anchors or just "#"
            if (hrefValue === "#" || !hrefValue) {
                return;
            }
            try {
                const targetId = hrefValue.substring(1); // Remove the # character
                const target = document.getElementById(targetId);
                
                if (target) {
                    e.preventDefault();
                    
                    window.scrollTo({
                        top: target.offsetTop - 100,
                        behavior: 'smooth'
                    });
                }
            } catch(error) {
                console.error("Smooth scroll error:", error);
            }
      
        });
    });
    
    // Animate elements on scroll
    const animateElements = document.querySelectorAll('.animate-on-scroll');
    
    if (animateElements.length > 0) {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -100px 0px'
        };
        
        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);
        
        animateElements.forEach(element => {
            observer.observe(element);
        });
    }
    
    // Resume counter animation
    const counterElement = document.querySelector('.counter-number');
    
    if (counterElement) {
        const finalValue = parseInt(counterElement.textContent.replace(/,/g, ''));
        const duration = 2000; // 2 seconds
        const framesPerSecond = 60;
        const totalFrames = duration / 1000 * framesPerSecond;
        const increment = finalValue / totalFrames;
        
        let currentValue = 0;
        let currentFrame = 0;
        
        const animate = () => {
            currentFrame++;
            currentValue += increment;
            
            if (currentFrame <= totalFrames) {
                counterElement.textContent = Math.floor(currentValue).toLocaleString();
                requestAnimationFrame(animate);
            } else {
                counterElement.textContent = finalValue.toLocaleString();
            }
        };
        
        // Start animation when element is in view
        const counterObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                animate();
                counterObserver.unobserve(counterElement);
            }
        }, { threshold: 0.5 });
        
        counterObserver.observe(counterElement);
    }
    
    // Flash message dismissal
    const flashMessages = document.querySelectorAll('.success, .danger, .warning, .info');
    
    flashMessages.forEach(message => {
        // Add close button
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '&times;';
        closeButton.className = 'flash-close';
        message.appendChild(closeButton);
        
        // Add dismissal functionality
        closeButton.addEventListener('click', () => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.style.display = 'none';
            }, 300);
        });
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.style.display = 'none';
            }, 300);
        }, 5000);
    });

    document.addEventListener('click', function(event) {
        // Toggle dropdown when clicking the toggle element
        if (event.target.closest('#user-dropdown-toggle')) {
            event.preventDefault();
            document.getElementById('user-dropdown').classList.toggle('active');
        } 
        // Close dropdown when clicking outside
        else if (!event.target.closest('#user-dropdown') && 
                document.getElementById('user-dropdown') && 
                document.getElementById('user-dropdown').classList.contains('active')) {
            document.getElementById('user-dropdown').classList.remove('active');
        }
    });
});
function showSaveIndicator() {
    const indicator = document.getElementById('save-indicator');
    if (indicator) {
        indicator.classList.add('show');
        setTimeout(() => {
            indicator.classList.remove('show');
        }, 3000);
    }
}

// Call this after successful form submission
document.querySelectorAll('.resume-form').forEach(form => {
    form.addEventListener('submit', function() {
        // Store in localStorage that form was submitted
        localStorage.setItem('formSubmitted', 'true');
    });
});
   // Check on page load if we should show the indicator
if (localStorage.getItem('formSubmitted') === 'true') {
    showSaveIndicator();
    localStorage.removeItem('formSubmitted');
}

const billingToggle = document.getElementById('billing-toggle');
if (billingToggle) {
    const monthlyPrices = document.querySelectorAll('.monthly-price');
    const annualPrices = document.querySelectorAll('.annual-price');
    const monthlyPeriods = document.querySelectorAll('.monthly-period');
    const annualPeriods = document.querySelectorAll('.annual-period');
    
    billingToggle.addEventListener('change', function() {
        if (this.checked) {
            // Annual billing
            monthlyPrices.forEach(el => el.style.display = 'none');
            annualPrices.forEach(el => el.style.display = 'inline');
            monthlyPeriods.forEach(el => el.style.display = 'none');
            annualPeriods.forEach(el => el.style.display = 'inline');
        } else {
            // Monthly billing
            monthlyPrices.forEach(el => el.style.display = 'inline');
            annualPrices.forEach(el => el.style.display = 'none');
            monthlyPeriods.forEach(el => el.style.display = 'inline');
            annualPeriods.forEach(el => el.style.display = 'none');
        }
    });
}

// Highlight the most popular plan on hover
const planCards = document.querySelectorAll('.plan-card');
planCards.forEach(card => {
    card.addEventListener('mouseover', function() {
        if (!this.classList.contains('popular')) {
            planCards.forEach(c => {
                if (c.classList.contains('popular')) {
                    c.classList.add('temporarily-unpopular');
                    c.classList.remove('popular');
                }
            });
        }
    });
    
    card.addEventListener('mouseout', function() {
        planCards.forEach(c => {
            if (c.classList.contains('temporarily-unpopular')) {
                c.classList.add('popular');
                c.classList.remove('temporarily-unpopular');
            }
        });
    });
});
// Add CSS for JavaScript-dependent styles
document.head.insertAdjacentHTML('beforeend', `
<style>
    .mobile-nav-toggle.active span:nth-child(1) {
        transform: translateY(9px) rotate(45deg);
    }
    
    .mobile-nav-toggle.active span:nth-child(2) {
        opacity: 0;
    }
    
    .mobile-nav-toggle.active span:nth-child(3) {
        transform: translateY(-9px) rotate(-45deg);
    }
    
    .main-nav.scrolled {
        padding: 0.75rem 0;
        background-color: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    body.nav-open {
        overflow: hidden;
    }
    
    .flash-close {
        position: absolute;
        top: 50%;
        right: 1rem;
        transform: translateY(-50%);
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        opacity: 0.5;
        transition: opacity 0.3s ease;
    }
    
    .flash-close:hover {
        opacity: 1;
    }
    
    .success, .danger, .warning, .info {
        position: relative;
        transition: opacity 0.3s ease;
    }
    
    /* Animation classes */
    .animate-on-scroll {
        opacity: 0;
        transform: translateY(30px);
        transition: opacity 0.6s ease, transform 0.6s ease;
    }
    
    .animate-visible {
        opacity: 1;
        transform: translateY(0);
    }
</style>
`);