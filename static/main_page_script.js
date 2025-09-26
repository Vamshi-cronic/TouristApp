document.addEventListener('DOMContentLoaded', function() {
    const header = document.querySelector('header');
    const backToTopButton = document.querySelector('.back-to-top');
    const hamburger = document.querySelector('.hamburger');
    const mainNav = document.querySelector('.main-nav');
    const navLinks = document.querySelectorAll('.main-nav a');
    const sections = document.querySelectorAll('main section');

    // --- SCROLL BASED INTERACTIONS ---
    const handleScroll = () => {
        // Scrolled Header
        header.classList.toggle('scrolled', window.scrollY > 50);

        // Back to top button
        backToTopButton.classList.toggle('visible', window.scrollY > 300);

        // Active nav link highlighting
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            if (window.pageYOffset >= sectionTop - header.clientHeight * 1.5) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(a => {
            a.classList.remove('active');
            // Check for href existence to avoid errors with non-anchor tags
            if (a.getAttribute('href') && a.getAttribute('href').substring(1) === current) {
                a.classList.add('active');
            }
        });
        // Set 'About' as active if at the top of the page
        if (window.scrollY < sections[0].offsetTop - header.clientHeight * 1.5) {
             const aboutLink = document.querySelector('nav a[href="#about"]');
             if(aboutLink) aboutLink.classList.add('active');
        }
    };
    
    // Run on load and on scroll
    handleScroll();
    window.addEventListener('scroll', handleScroll);

    // --- HAMBURGER MENU ---
    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        mainNav.classList.toggle('active');
    });
    
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
             if (mainNav.classList.contains('active')) {
                hamburger.classList.remove('active');
                mainNav.classList.remove('active');
             }
        });
    });

    // --- INTERSECTION OBSERVER FOR FADE-IN ANIMATIONS ---
    const sectionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                sectionObserver.unobserve(entry.target); 
            }
        });
    }, { threshold: 0.15 });

    document.querySelectorAll('.content-section').forEach(section => {
        sectionObserver.observe(section);
    });
    
    // --- COUNTER UP ANIMATION ---
    const counterObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counters = entry.target.querySelectorAll('.counter');
                counters.forEach(counter => {
                    counter.innerText = '0';
                    const target = +counter.getAttribute('data-target');
                    // Calculate increment to make animation last roughly the same time
                    const increment = target / 100;

                    const updateCounter = () => {
                        const c = +counter.innerText;
                        if (c < target) {
                            counter.innerText = `${Math.ceil(c + increment)}`;
                            requestAnimationFrame(updateCounter);
                        } else {
                            counter.innerText = target.toLocaleString(); // Add commas for larger numbers
                        }
                    };
                    updateCounter();
                });
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    const statsSection = document.getElementById('stats');
    if(statsSection) {
        counterObserver.observe(statsSection);
    }
    
    // --- FORM SUBMISSION HANDLING (EXAMPLE) ---
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent page reload
            // Here you would add code to send form data via fetch/AJAX
            alert('Thank you for your message! (Form submission is a demo)');
            contactForm.reset(); // Clear the form
        });
    }
});