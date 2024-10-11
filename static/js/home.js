const toggleButton = document.getElementById('theme-toggle');
const body = document.body;
const header = document.querySelector('header');
const sections = document.querySelectorAll('.section');
const footer = document.querySelector('footer'); //Include footer information

// Check user preference and set the theme
const currentTheme = localStorage.getItem('theme') || 'light';
if (currentTheme === 'dark') {
    body.classList.add('dark');
    header.classList.add('dark');
    sections.forEach(section => section.classList.add('dark'));
    footer.classList.add('dark'); //Add the dark mode capability to the footer 
    toggleButton.textContent = 'Toggle Light Mode';
}

// Theme toggle functionality
toggleButton.addEventListener('click', () => {
    body.classList.toggle('dark');
    header.classList.toggle('dark');
    sections.forEach(section => section.classList.toggle('dark'));
    footer.classList.toggle('dark'); //Enable the dark mode class for the footer

    const isDarkMode = body.classList.contains('dark');
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    toggleButton.textContent = isDarkMode ? 'Toggle Light Mode' : 'Toggle Dark Mode';
});

