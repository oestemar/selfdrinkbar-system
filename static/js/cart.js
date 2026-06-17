console.log('cart.js loaded');
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll('.add-to-cart').forEach(btn => {
        btn.addEventListener('click', async () => {
            const itemId = btn.dataset.id;

            const formData = new FormData();
            formData.append('item_id', itemId);
            formData.append('quantity', 1);

            const res = await fetch('/cart/add', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();

            if (data.success) {
                const cartCount = document.getElementById('cart-count');
                if (cartCount) {
                    cartCount.textContent = data.cart_count;
                }
            } else {
                alert(data.message);
            }
        });
    });
});
