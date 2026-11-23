/* 全站通用脚本 */
(function ($) {
    "use strict";

    // AJAX 统一携带 CSRF Token（从 cookie 中读取）
    function getCookie(name) {
        var value = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
        return value ? decodeURIComponent(value.pop()) : "";
    }

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS)$/.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
            }
        }
    });
})(jQuery);
