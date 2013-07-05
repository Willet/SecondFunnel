# Setup script for importing the themes into the Django DB
# Since we don't want to have to copy over the HTML each time and maintain an updated
# copy of the themes, this script will allow us to update/import the themes from our
# local git theming repository.
import os, string, re

from django.core.management.base import NoArgsCommand

from apps.pinpoint.models import StoreTheme


class Command (NoArgsCommand):
    help = "Imports the SecondFunnel themes and creates new themes or updates existing ones."

    def handle_noargs(self, **kwargs):
        try:
            REPO = str(raw_input("Enter the location of the SecondFunnel Theming Directory: "))
            if not os.path.isdir(REPO):
                raise TypeError
            else:
                if not REPO.endswith(os.path.sep):
                    REPO += os.path.sep
                self.updateThemes(REPO)
        except TypeError:
            print "Specified directory does not exist."
            exit(1)

    def readfile(self, filepath):
        output = ""
        with open(filepath, 'r') as source:
            output = source.read()
        return output

    def update(self, dir, files, name):
        # Create or update the theme.  Update if it exists, otherwise create it.
        theme, attributes = None, [field.name for field in StoreTheme._meta.fields]
        try:
            # Attempt to retrive the theme, if successful, update it, otherwise create a
            # new one.
            theme = StoreTheme.objects.get(name=name)
            print "Updating theme for %s..."%(name),
            for file in files:
                try:
                    attr = file.replace(".html", "").replace("-", "_")
                    setattr(theme, attr, self.readfile(os.path.join(dir, file)))
                except AttributeError:
                    pass
        except StoreTheme.DoesNotExist:
            print "Creating new theme for %s..."%(name),
            required = {'name': name }
            for file in files:
                attr = file.replace(".html", "").replace("-", "_")
                if attr in attributes:
                    required[attr] = self.readfile(os.path.join(dir, file))
            if len(required) <= 1:
                return None
            theme = StoreTheme(**required) 
        print "Done"
        theme.save()


    def updateThemes(self, dir):
        themeDirectories = [ directory for directory in os.walk(dir).next()[1] if directory[0] != "." and directory.lower() != "example" ]
        for theme in themeDirectories:
            walk = os.walk(os.path.join(dir, theme)).next()
            if len(walk[1]) > 0:
                for directory in walk[1]:
                    themeDirectories.append(os.path.join(theme, directory))
            elif len(walk[2]) > 0:
                # Found a theme directory, generate the name and create the theme.
                name = re.sub(r'([' + string.ascii_uppercase + '])', r' \1', theme).replace("/", "").replace("Gap", "GAP")
                if not("Mobile" in name or "Desktop" in name):
                    name += " Default Theme"
                else:
                    name += " Theme"
                self.update(os.path.join(dir, theme), walk[2], name[1:])

