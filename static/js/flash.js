
    document.addEventListener('DOMContentLoaded', () => {
      const flashes = document.querySelectorAll('.alert');
      flashes.forEach((flash, i) => {
        setTimeout(() => flash.classList.add('show'), i * 100);
        setTimeout(() => flash.style.display = 'none', 5000);
      });
    });
