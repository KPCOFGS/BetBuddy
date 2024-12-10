document.addEventListener("DOMContentLoaded", function () {
        const modal = document.getElementById("modal");
        const closeModal = document.getElementById("closeModal");

        // Show the modal automatically when the page loads
        modal.style.display = "block";

        // Close the modal when the close button is clicked
        closeModal.onclick = function () {
            modal.style.display = "none";
        };

        // Close the modal if the user clicks outside of it
        window.onclick = function (event) {
            if (event.target == modal) {
                modal.style.display = "none";
            }
        };
    });
