---
$title: Try Grow
$category: Get Started
$order: 3
foo: bar
animals:
- name: kevin
  kind: dog
- name: zacky
  kind: cat
---
# Got 15 minutes? Give Grow a spin.

This *Try Grow* tutorial will walk you through the basics of using the Grow Site Development Kit (SDK). Here, you'll learn how to create a site using the SDK, explore how it works and learn about how your site is built, add some content, and deploy it to the public.

## 0. Download

Before you begin, you'll have to download the Grow SDK. Don't worry, the Grow SDK is __light, fully encapsulated, and portable__. To install the Grow command (`grow`) to your computer, download the file below, open *Grow SDK.app*, and confirm the symlink installation.

<div class="well">
  <p><a class="btn btn-lg btn-primary" href="https://github.com/grow/macgrow/releases">Download the Grow SDK (Mac)</a>
  <div><b>Current version: PRE-RELEASE 0.0.1</b></div>
</div>

The Grow SDK for Mac is distributed as a Mac app. [The code for this app is open source](https://github.com/grow/macgrow). Prefer to use a package manager? Disregard the above and just `pip install grow`.

## 1. Initialize

Now that you've got Grow on your computer, you're ready to start building your first site. Grow takes a set of files in various formats that are arranged in specific folder structure, runs them through a few processing steps, and builds a complete, ready-to-serve web site.

In Grow, sites are organized into directories called __pods__. So, each site is stored in one __pod__.

Open up a command prompt. Run the following command, which initializes a basic pod for you in a directory it creates named `hello-grow`.

    grow init hello-grow https://github.com/growthemes/try-grow.git

Now you'll have a pod in the `hello-grow` folder.

## 2. Explore 

Let's take a quick look at what actually is in this pod. Here's the directory structure that was just created:

    /content
      /pages
        /_blueprint.yaml
        /hello-grow.md
        /index-grow.md
    /media
    /translations
    /views
      /_base.html
    /podspec.yaml

- __/content__: Holds *content collections*, which include *blueprints* and *content documents*. Content documents are Markdown files with YAML front matter.
- __/media__: Holds directly-servable "media" files for your site. This includes JavaScript, CSS, images, etc.
- __/translations__: Holds translatable strings extracted from content and views, stored in the PO file format.
- __/views__: Holds Jinja2 HTML templates, used to render your pages.
- __/podspec.yaml__: Pod specification file, which contains a configuration that describes your pod.

Again, how Grow builds and serves your site is determined by the files and folders in your pod.

## 3. Preview 

OK, before we add or remove anything to your site, let's get a preview of your pod running so you can try "edit and refresh" development. The following command will start up a local Grow server that will build and serve your new pod. By default, it also opens up a web browser to the pod's home URL.

    grow run hello-grow

You may navigate around the basic web site. Again, this site is built from the files in your pod.

## 4. Create

Adding a new page to your site is as easy as adding a new content document file. Content documents are the Markdown files in your pod's __content__ folder. The combination of __blueprints__ and __views__ determine things like how your content documents are served, the way they look, whether they appear in navigation menus, and their URLs.

OK, create a new file __/content/pages/my-page.md__.

    --
    $title: My New Page
    --
    # Welcome!

    This is my new page.

Now we'll take a moment to explain what this means:

- You just created a content document whose slug is __my-page__.
- The stuff between the three dashes (--) at the top of the file is called YAML front matter. Everything between the dashes must be YAML-formatted. Everything below the dashes is markdown.
- The key __$title__ is the document's human-readable title.
  - Front matter fields that start with a dollar sign (__$__) are fields that are built-in to Grow and may be used by the system to control things like a document's URL path (more on this later).
  - Fields that do NOT start with a dollar sign are custom fields that you specify. Custom fields can be accessed by a content document's view (more on this later too).

Check out your newly-added page. Just refresh your browser and you'll see the page automatically added to the navigation menu. Click the link to the page to view it.

### 4.1 Customize the URL

Clean URLs are important, and having absolute control over your site's URLs is an important feature in Grow. Each document has its own URL, derived from rules specified in the document itself, and the document's blueprint.

Let's take a moment to see how this document's URL is determined. Open up the file __/content/pages/_blueprint.yaml__ and notice the following line:

    path: /{slug}/

This indicates that the URLs documents in the __pages__ collection should be determined by their slugs. Remember, the content document __/content/pages/try-grow.md__'s slug is __try-grow__, so this document's URL path is __/try-grow/__.

Now let's try customizing the URL further. A content document can override its blueprint's path by specifyine one itself. Open __/content/pages/my-page.md__ again. Change the front matter to the following.

    $title: My New Page
    $path: /custom-url-for-my-page/

Navigate to __/custom-url-for-my-page/__ in the browser to see the change. This content document is now specifying its own URL.

### 4.2 Hide content

Not all content in your site may have its own URL – some content may just be referenced within other content and may not be designed to stand alone.

If both a content document and its blueprint do not have a `$path` and `path` field, respectively, the content will NOT be made available as a standalone page.

Individual content documents can also be marked as hidden to prevent them from being served and from being included in automatically-generated navigation menus. This is done using the `$hidden` field.

Change the front matter of __/content/pages/my-page.md__ to the following:

    $title: My New Page
    $path: /custom-url-for-my-page/
    $hidden: yes

The page built from this content document is now hidden, inaccessible directly and hidden from navigation menus.

## 5. Translate

Grow was built from the start to include powerful localization features, in order to make it as a easy as possible to localize your web sites. Using Grow, you can translate your content, translate your views, manage the translations separately from the sources, and build localized versions of your site.

## 6. Design

## 7. Build

## 8. Launch

## 9. Next steps

Now that you've gone through this tutorial, the next article you should read is the Grow pod specification ("podspec"). The podspec covers all the capabilities of Grow and describes everything you need to know regarding how to encapsulate your site's content, templates, media, data files, etc.

<a class="btn btn-primary">Next: Directory structure</a>
