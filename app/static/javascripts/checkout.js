$(document).ready(function () {
    const $citySelect = $('#city');
    const $districtSelect = $('#district');
    const $wardSelect = $('#ward');
    const userAddress = "{{ user.address or '' }}";

    // Hàm lấy danh sách tỉnh/thành
    function loadCities() {
        $.ajax({
            url: 'https://provinces.open-api.vn/api/?depth=1',
            method: 'GET',
            success: function (cities) {
                cities.forEach(city => {
                    const isSelected = userAddress.includes(city.name) ? 'selected' : '';
                    $citySelect.append(`<option value="${city.name}" ${isSelected}>${city.name}</option>`);
                });
                $citySelect.prop('disabled', false);
                if ($citySelect.val()) loadDistricts(); // Tải quận/huyện nếu có giá trị mặc định
            },
            error: function (error) {
                console.error('Lỗi khi tải danh sách tỉnh/thành:', error);
            }
        });
    }

    // Hàm lấy danh sách quận/huyện dựa trên tỉnh/thành
    function loadDistricts() {
        $districtSelect.html('<option value="" disabled selected>Chọn quận / huyện</option>');
        $wardSelect.html('<option value="" disabled selected>Chọn phường / xã</option>');
        $districtSelect.prop('disabled', true);
        $wardSelect.prop('disabled', true);

        const selectedCity = $citySelect.val();
        if (!selectedCity) return;

        $.ajax({
            url: 'https://provinces.open-api.vn/api/?depth=2',
            method: 'GET',
            success: function (data) {
                const cityData = data.find(city => city.name === selectedCity);
                if (cityData && cityData.districts) {
                    cityData.districts.forEach(district => {
                        const isSelected = userAddress.includes(district.name) ? 'selected' : '';
                        $districtSelect.append(`<option value="${district.name}" ${isSelected}>${district.name}</option>`);
                    });
                    $districtSelect.prop('disabled', false);
                    if ($districtSelect.val()) loadWards(); // Tải phường/xã nếu có giá trị mặc định
                }
            },
            error: function (error) {
                console.error('Lỗi khi tải danh sách quận/huyện:', error);
            }
        });
    }

    // Hàm lấy danh sách phường/xã dựa trên quận/huyện
    function loadWards() {
        $wardSelect.html('<option value="" disabled selected>Chọn phường / xã</option>');
        $wardSelect.prop('disabled', true);

        const selectedDistrict = $districtSelect.val();
        if (!selectedDistrict) return;

        $.ajax({
            url: 'https://provinces.open-api.vn/api/?depth=3',
            method: 'GET',
            success: function (data) {
                const cityData = data.find(city => city.name === $citySelect.val());
                if (cityData) {
                    const districtData = cityData.districts.find(district => district.name === selectedDistrict);
                    if (districtData && districtData.wards) {
                        districtData.wards.forEach(ward => {
                            const isSelected = userAddress.includes(ward.name) ? 'selected' : '';
                            $wardSelect.append(`<option value="${ward.name}" ${isSelected}>${ward.name}</option>`);
                        });
                        $wardSelect.prop('disabled', false);
                    }
                }
            },
            error: function (error) {
                console.error('Lỗi khi tải danh sách phường/xã:', error);
            }
        });
    }

    $citySelect.on('change', loadDistricts);
    $districtSelect.on('change', loadWards);

    // Tải danh sách tỉnh/thành khi trang được tải
    loadCities();
});