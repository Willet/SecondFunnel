var application = (function(store_id, products, urls){
    var $pageChanged = $('#id_page_changed'),
        createUploader,
        productSelected,
        setProductFields,
        updateCharacterCount,
        ready,
        init,
        getAutoCompleteConfig,
        onPageChanged,
        onImageSelect,
        onExistingImageSelect,
        onNewImageSelect,
        onPreview,
        onCancel,
        onBack,
        UPPER_CHARACTER_LIMIT   = 250,
        UPPER_CHARACTER_WARNING = 230,
        LOWER_CHARACTER_WARNING = 20;

    setProductFields = function (product, data) {
        // set product's proper name
        $("#product_name").val(product.name);

        if (!data.human_invoked) {
            $("#id_name").val(data.page_name);
        } else {
            // resetting previous values
            $("#id_product_media_id").val("");
            $("#id_generic_media_id").val("");
            $("#id_generic_media_lst").val("");

            //TODO: Why here?
            onPageChanged();

            $("#id_name").val("Featured: " + product.name);
        }

        // fire change event so validator updates
        $("#id_name").change();

        $("#id_description").val(data.product_description || product.description);

        // fire change event so validator updates
        $("#id_description").change();

        // set the id for form submission
        $("#id_product_id").val(product.id);

        // update character count
        updateCharacterCount();
    };

    productSelected = function(data) {
        var product = products[data.product_id],
            media_id = $("#id_product_media_id").val(),
            li, uploadedImages;

        // Hide errors
        // TODO: Which image selector
        $("#image-selector").siblings(".errorlist").children("li").fadeIn(500);

        if (typeof(product) === "undefined") {
            return;
        }

        // clear existing image list
        // TODO: Which images?
        images = $("#product_images li");
        imagesToRemove = images.splice(1, images.length - 1);
        for (var i = imagesToRemove.length - 1; i >= 0; i--) {
            $(imagesToRemove[i]).remove();
        }

        // display product media
        for (i in product.media) {
            li = $("<li><img class='prod_img existing_image' data-mid='" + product.media[i].id + "' src='" + product.media[i].url + "'></li>");
            if (product.media[i].id == data.product_image_id) {
                // TODO: which image selector?
                $("#image-selector").siblings(".errorlist").children("li").hide();
                li.children('img').addClass('selected');
            }
            $("#product_images").append(li);
        }

        if (data.product_generic_image_list) {
            uploadedImages = $.map(
                data.product_generic_image_list.split("|"),
                function(str) {
                    var s = str.split("\\"); return {url: s[0], id: s[1]};
                }
            );
            $.map(uploadedImages.reverse(), function(img) {
                var image = $("<li><img class='prod_img new_image' data-mid='" + img.id + "' src='" + img.url + "'></li>");
                if (data.product_generic_image_id == img.id) {
                    $("#image-selector").siblings(".errorlist").children("li").hide();
                    image.children('img').addClass('selected');
                }
                $("#fine-uploader").closest('li').after(image);
            });
        }

        // #TODO: Which product_images?
        $("#product_images").find("[data-mid='" + media_id  + "']").addClass("selected")

        // Update other product fields
        setProductFields(product, data)

        $(".product_meta").unmask();
    };

    updateCharacterCount = function() {
        var $textarea   = $('#id_description'),
            length      = $textarea.val().length,
            $characters = $('#characters'),
            $count      = $('#character_count'),
            $buttons    = $('.button:not(#cancel_to_admin, .back, .qq-upload-button)'),
            error,
            low_warning,
            high_warning,
            warning;

        error        = (UPPER_CHARACTER_LIMIT <= length) || (length == 0);
        high_warning = (UPPER_CHARACTER_WARNING <= length && length < UPPER_CHARACTER_LIMIT);
        low_warning  = (0 < length && length <= LOWER_CHARACTER_WARNING)
        warning      = low_warning || high_warning;

        $characters.text(length);
        $count.removeClass();
        $buttons.removeClass('disabled');
        $buttons.removeAttr('disabled');

        if (error) {
            $count.addClass('danger');
            $buttons.addClass('disabled');
            $buttons.attr('disabled', 'disabled');
        } else if (warning) {
            $count.addClass('warning');

            if (low_warning && $('#small_desc_warning:hidden')) {
                $('#small_desc_warning:hidden').fadeIn(500);
            }
        } else {
            $('#small_desc_warning').stop(true, true);
            $('#small_desc_warning').fadeOut(500);
        }
    };

    onPageChanged = function() {
        $pageChanged.val('true');
    };

    getAutoCompleteConfig = function () {
        return {
            source: function(request, response) {
                var term = request.term;
                $.getJSON('/api/assets/v1/product/', {
                    'store': store_id,
                    'format': 'json',
                    'name_or_url': term

                }, function(data) {
                    //convert object to usable form
                    var results = [];
                    $.each(data.objects, function(index, value) {
                        results.push({'label': value.name, 'id': value.id})
                    });
                    response(results);
                })
            },
            minLength: 2,
            select: function( event, ui ) {
                if (ui.item) {
                    productSelected({
                        product_id: ui.item.id,
                        human_invoked: true
                    });
                }
            }
        };
    };

    onImageSelect = function ($elem, existing) {
        var $image = $elem;

        // Hide related errors
        // TODO:
        $('#image-selector').siblings('.errorlist').children('li').fadeOut(500);

        $image.parents('.product-images').find('img').removeClass('selected');
        $image.addClass('selected');

        if (existing) {
            $('#id_product_media_id').val($image.data('mid'));
            $('#id_generic_media_id').val('');
        } else {
            $('#id_generic_media_id').val($image.data('mid'));
            $('#id_product_media_id').val('');
        }
    };

    onExistingImageSelect = function () {
        onImageSelect($(this), true);
    };

    onNewImageSelect = function () {
        onImageSelect($(this), false);
    };

    onPreview = function () {
        var $form = $('#create_campaign'),
            $campaign_id = $('#id_campaign_id');

        $.ajax({
            async: false,
            type: 'POST',
            data: $form.serialize(),
            url: window.location.href,
            success: function(response) {
                if (response.success) {
                    var url = 'http://' + window.location.host + response.url;
                    window.open(url, '_blank');
                    $campaign_id.val(response.campaign);
                } else {
                    $form[0].submit();
                }
            }
        })
    };

    onCancel = function(){
        var cancel;

        if ($pageChanged.val()) {
            cancel = confirm('Are you sure you want to cancel your ' +
                'changes?');
        }

        if (cancel || !$pageChanged.val()) {
            window.location.href = urls['store-admin'];
        }
    };

    onBack = function(){
        var cancel;

        if ($pageChanged.val()) {
            cancel = confirm('By going back you will lose your ' +
                'changes on this page. Are you sure?');
        }

        if (cancel || $pageChanged.val()) {
            window.location.href = urls['new-campaign-admin'];
        }
    };

    createUploader = function($elem) {
        var uploader,
            $productImages = $elem.parents('.product-images');

        uploader = new qq.FileUploader({
            element: $elem[0],
            action: urls['ajax-image-upload'],
            csrfToken: $.cookie('csrftoken'),
            allowedExtensions: ['jpg' ,'png', 'jpeg'],
            onSubmit: function() {
                $elem.closest('li').after(
                    '<li><img class=\'loading_gif\' src=\'' +
                        urls['loading-gif'] +
                        '\'></li>'
                );
            },
            onComplete: function(id, fileName, response) {
                var decodedUrl, gif, li;

                if (response.success) {
                    decodedUrl = $(document.createElement('div')).html(response.url).text();
                    gif = $productImages.find('.loading_gif');

                    gif.hide();
                    gif.removeClass('loading_gif');
                    gif.addClass('prod_img');
                    gif.addClass('new_image');
                    gif.attr('src', decodedUrl);
                    gif.data('mid', response.media_id);
                    gif.load(function() {
                        gif.fadeIn(500);
                        gif.click();
                    });
                    $("#id_generic_media_list").val($('#product_images img.new_image').map(
                        function(){return $(this).attr('src') + "\\" + $(this).data('mid');}).toArray().join("|"));
                } else {
                    gif = $productImages.find('.loading_gif');
                    li = gif.closest('li');
                    li.addClass('broken_image');
                    gif.remove();
                    li.html('<div class="rounded"><ul class="errorlist"><li>Error uploading image.</li><br /><li>Click this box to dismiss.</li></ul></div>')

                    $("li.broken_image").on('click', function() {
                        $(this).animate({
                            width: 0,
                            margin: 0,
                            padding: 0
                        }, 500, function() {
                            $(this).remove();
                        });
                    });
                }
            }
        });

        return uploader;
    };

    ready = function() {
        $('#id_description').on('keydown keyup', updateCharacterCount);
        $('#product_name').autocomplete(getAutoCompleteConfig());
        $('.button.preview').on('click', onPreview);
        $('#cancel_to_admin').on('click', onCancel);
        $('.button.back:not(.disabled)').on('click', onBack);

        $('#product_images').on('click', 'img.existing_image', onExistingImageSelect);
        $('#product_images').on('click', 'img.new_image', onNewImageSelect);

        // Trigger page changed events
        $('#product_images').on('click', 'img.existing_image', onPageChanged);
        $('#product_images').on('click', 'img.new_image', onPageChanged);
        $('#id_name, #id_description').change(onPageChanged);
        $('#id_name, #id_description').keyup(onPageChanged);
    };

    init = function() {
        var uploader;

        $(".product_meta").mask();
        $("#product_name").watermark("Your product name");
        $("#id_name").watermark("Your page name");
        $("#id_description").watermark("Featured product description");

        $(document).ready(ready);

        //create uploaders
        uploader = createUploader($('#fine-uploader'));

        // select product
        productSelected({
            product_id                : $("#id_product_id").val(),
            page_name                 : $("#id_name").val(),
            product_description       : $("#id_description").val(),
            product_image_id          : $("#id_product_media_id").val(),
            product_generic_image_id  : $("#id_generic_media_id").val(),
            product_generic_image_list: $("#id_generic_media_list").val()
        });

        $(".qq-upload-button").addClass('button');
    };

    return {
        'init': init
    }

})(window.store, window.product_information || {}, window.url_list || {});

application.init();