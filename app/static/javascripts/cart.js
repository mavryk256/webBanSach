$(document).ready(function () {
    // Hàm chọn hoặc bỏ chọn tất cả checkbox
    function toggleSelectAll() {
        const selectAllCheckbox = document.getElementById('select-all');
        if (!selectAllCheckbox) return;

        const orderCheckboxes = document.querySelectorAll('.order-checkbox');
        orderCheckboxes.forEach(checkbox => {
            checkbox.checked = selectAllCheckbox.checked;
        });
        updateTotalSelected();
    }

    // Hàm cập nhật tổng tiền của các đơn hàng được chọn
    function updateTotalSelected() {
        let total = 0;
        const orderCheckboxes = document.querySelectorAll('.order-checkbox:checked');
        orderCheckboxes.forEach(checkbox => {
            const totalValue = parseFloat(checkbox.getAttribute('data-total')) || 0;
            total += totalValue;
        });

        const selectedTotalElement = document.getElementById('selected-total');
        if (selectedTotalElement) {
            selectedTotalElement.textContent = total.toLocaleString('vi-VN');
        }

        const checkoutBtn = document.getElementById('checkout-btn');
        if (checkoutBtn) {
            checkoutBtn.disabled = orderCheckboxes.length === 0;
        }
    }

    // Hàm cập nhật số lượng đơn hàng
    function updateQuantity(orderId, change) {
        const quantityInput = document.getElementById(`quantity-${orderId}`);
        if (!quantityInput) return;

        let newQuantity = parseInt(quantityInput.value) + change;
        if (newQuantity < 1) newQuantity = 1;
        quantityInput.value = newQuantity;

        $.ajax({
            url: `/cart/update/${orderId}`,
            method: 'POST',
            data: { quantity: newQuantity },
            success: function (response) {
                if (response.success) {
                    const totalPriceElement = document.getElementById(`total-price-${orderId}`);
                    if (totalPriceElement) {
                        totalPriceElement.textContent = `${response.total_price.toLocaleString('vi-VN')} VND`;
                    }

                    const checkbox = document.querySelector(`input[name="selected_orders"][value="${orderId}"]`);
                    if (checkbox) {
                        checkbox.setAttribute('data-total', response.total_price);
                    }
                    updateTotalSelected();
                } else {
                    alert(response.message);
                    quantityInput.value = parseInt(quantityInput.value) - change;
                }
            },
            error: function (error) {
                console.error('Lỗi khi cập nhật số lượng:', error);
                quantityInput.value = parseInt(quantityInput.value) - change;
            }
        });
    }

    // Gắn sự kiện cho checkbox "Chọn tất cả"
    const selectAll = document.getElementById('select-all');
    if (selectAll) {
        selectAll.addEventListener('change', toggleSelectAll);
    }

    // Gắn sự kiện cho các checkbox đơn hàng
    document.querySelectorAll('.order-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateTotalSelected);
    });

    // Gắn hàm updateQuantity vào window để gọi từ HTML
    window.updateQuantity = updateQuantity;

    // Cập nhật tổng tiền ban đầu
    updateTotalSelected();
});