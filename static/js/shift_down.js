document.addEventListener('DOMContentLoaded', function() {
    if (document.body.scrollHeight <= window.innerHeight) {
      document.querySelector('main').style.marginTop = 'calc(120px)';
    }
});
