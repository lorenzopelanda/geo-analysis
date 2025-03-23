document.addEventListener('DOMContentLoaded', function() {
    var header = document.querySelector('.page-header');
    if (header) {
      header.style.backgroundImage = "url('assets/images/background.jpg')";
      header.style.backgroundSize = "cover";
      header.style.backgroundPosition = "center";
      header.style.backgroundBlendMode = "overlay";
    }
  });