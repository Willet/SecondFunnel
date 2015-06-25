'use strict'

# @module core.views

module.exports = (module, App, Backbone, Marionette, $, _) ->
    # For Sur La Table, the "content" image is the best looking product image
    # Re-order the product images so that image is first
    # For desktop, hide it because the pop-up will show the content image
    # For mobile, we will show the product image in leui of showing the content image
    _.extend module.ExpandedContent.prototype, 
        reorderProductImages: ->
            try 
                imageUrl = @model.attributes.url
                prodImages = @model.attributes['tagged-products'][0].images
            catch err
                # One of the required objects in the accessor chains doesn't exist
                return
            if imageUrl and prodImages
                matchImgObj = _.find prodImages, (imgObj) ->
                    # Remove Cloudinary url API operations before doing url comparison
                    # .../upload/c_fit,q_75,w_700/v... -> .../upload/v...
                    baseImgUrl = imgObj.url.replace /(upload)(.*)(\/v)/, "$1$3"
                    return  (baseImgUrl == imageUrl)

                if matchImgObj
                    # prodImages is a reference, will modify product images in place
                    matchImgObjIndex = prodImages.indexOf(matchImgObj)
                    matchImgObj = prodImages.splice(matchImgObjIndex, 1)[0]
                    # Add back as 1st piece of content on mobile because there
                    # is only one gallery on mobile
                    if App.support.mobile()
                        prodImages.unshift(matchImgObj);

        coreRenderSubregions: module.ExpandedContent.prototype.renderSubregions

        # Patch PreviewWindow content to order the "content" image first
        renderSubregions: ->
            @reorderProductImages()
            @coreRenderSubregions.apply @, arguments

    ###
    View responsible for the Sur La Table Hero Area
    This Hero's are special in that they use the same background images
    and overlay with text: GIFTS for ____ (ex: The Chef, Him)
    
    @constructor
    @type {LayoutView}
    ###
    class module.SLTHeroAreaView extends Marionette.LayoutView
        model: module.Tile
        className: "previewContainer"
        template: "#hero_template"
        regions:
            content: ".content"

        generateHeroArea: ->
            category = App.intentRank.currentCategory() || App.option('page:home:category')
            catObj = App.categories.findModelByName(category)

            # If category can't be found, default to 'The Chef'
            if not catObj? then catObj = displayName: 'The Chef'

            tile =
                desktopHeroImage: "/static/light/surlatable/landingpage/default/images/slt-hero-desktop.png"
                mobileHeroImage: "/static/light/surlatable/landingpage/default/images/slt-hero-desktop.png"
                title: "<span class='spaced'>GIFTS</span> <span class='for'>for #{catObj.displayName}</span>"
            
            if @model? and @model.destroy then @model.destroy()
            @model = new module.Tile(tile)
            return @

        loadHeroArea: ->
            @generateHeroArea()
            # If view is already visible, update with new category
            if not @.isClosed
                App.heroArea.show @

        initialize: ->
            if App.intentRank.currentCategory and App.categories
                @generateHeroArea()
            else
                # placeholder to stop error
                @model = new module.Tile()
                App.vent.once('intentRankInitialized', =>
                    @loadHeroArea()
                )
            @listenTo App.vent, "change:category", =>
                @loadHeroArea()
            return @

            
