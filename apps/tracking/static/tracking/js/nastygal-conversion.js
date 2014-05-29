// jshint ignore: start
var ClickMeter_conversion_value,
    ClickMeter_conversion_id = '271C54CB40964B26BD0593C4E24EF1C3',
    ClickMeter_conversion_commission = '0.00',
    ClickMeter_conversion_parameter = 'empty',
    convId;

function guessPrice() {
    var price;

    if (window.s_amc_hb) {
        try {
            price = window.s_amc_hb.contextData.hb_orderData_totalPrice.toString();
        } catch (e) {}
        try {
            if (!price) {
                price = window.s_amc_hb.contextData.hb_cartData_totalPrice.toString();
            }
        } catch (e) {}
        try {
            if (!price) {
                price = window.s_amc_hb.hb_orderData_totalPrice.toString();
            }
        } catch (e) {}
        try {
            if (!price) {
                price = window.s_amc_hb.hb_orderData_totalPrice.toString();
            }
        } catch (e) {}
    }
    if (window.dataLayer && window.dataLayer.length) {
        try {
            if (!price) {
                price = window.dataLayer[0].transactionTotal.toString();
            }
        } catch (e) {}
    }
    return price;
}

function getParam(name) {
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regexS = "[\\?&]" + name + "=([^&#]*)";
    var regex = new RegExp(regexS);
    var scripts = document.getElementsByTagName('script');
    var index = scripts.length - 1;
    var myScript = scripts[index];
    var results = regex.exec(myScript.src.toLowerCase());
    if (results == null) {
        return "";
    } else {
        return results[1];
    }
}

function loadPage() {
    var params = '';
    if (typeof ClickMeter_conversion_value !== 'undefined' && ClickMeter_conversion_value != null) {
        var convValue = parseFloat(ClickMeter_conversion_value.replace(',', '.'));
        if (!isNaN(convValue)) {
            params = '&val=' + convValue;
        }
    }
    if (typeof ClickMeter_conversion_parameter !== 'undefined' && ClickMeter_conversion_parameter != null && ClickMeter_conversion_parameter != '') {
        params = params + '&param=' + ClickMeter_conversion_parameter;
    }
    if (typeof ClickMeter_conversion_id !== 'undefined' && ClickMeter_conversion_id != null && ClickMeter_conversion_id != '') {
        convId = ClickMeter_conversion_id;
    }
    var panel = document.createElement('div');
    panel.setAttribute('id', 'conversion_container');
    panel.style.height = '0px';
    panel.style.width = '0px';
    panel.style.overflow = 'hidden';

    var iFrame = document.createElement('iframe');

    if ("https:" === document.location.protocol) {
        iFrame.setAttribute('src', 'https://clickmeter.com/conversion.aspx?id=' + convId + params);
    } else {
        iFrame.setAttribute('src', 'http://clickmeter.com/conversion.aspx?id=' + convId + params);
    }

    iFrame.setAttribute('frameborder', '0');
    iFrame.setAttribute('height', '0');
    iFrame.setAttribute('width', '0');
    iFrame.setAttribute('noresize', '0');
    iFrame.setAttribute('id', 'convframe');
    iFrame.setAttribute('name', 'convframe');
    iFrame.setAttribute('allowtransparency', 'true');
    var scripts = document.getElementsByTagName('script');
    var index = scripts.length - 1;
    var myScript = scripts[index];
    panel.appendChild(iFrame);
    myScript.parentNode.appendChild(panel);
    if (typeof ClickMeter_conversion_value !== 'undefined') {
        ClickMeter_conversion_value = null;
    }
    if (typeof ClickMeter_conversion_parameter !== 'undefined') {
        ClickMeter_conversion_parameter = null;
    }
    if (typeof ClickMeter_conversion_id !== 'undefined') {
        ClickMeter_conversion_id = null;
    }
}

ClickMeter_conversion_value = guessPrice();
ClickMeter_conversion_id = '271C54CB40964B26BD0593C4E24EF1C3';
ClickMeter_conversion_commission = '0.00';
ClickMeter_conversion_parameter = 'empty';
convId = getParam('id');

loadPage();
// jshint ignore: end
