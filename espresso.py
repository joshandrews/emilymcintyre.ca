#!/usr/bin/env python

def generateHeader(name):
    htmlStr = """$def with ()
    <div id="header">
        <div id="st-trigger-effects" class="column">
            <button class="nav-btn" data-effect="st-effect-4"></button>
        </div>
        <div class="name">
            <a href="/" class="button">
                <img src="/static/images/coffee.svg"/>
    """+name+"""
            </a>
        </div>
        <ul class="nav cl-effect-1">
            <li class="button">
                <a href="/blog" class="button">Blog</a>
            </li>
            <li class="button">
                <a href="/work" class="button">What I do</a>
            </li>
        </ul>
    </div>"""
    Html_file= open("templates/common/header.html","w")
    Html_file.write(htmlStr)
    Html_file.close()
    htmlStrad = """$def with ()
    <div id="header">
        <div id="st-trigger-effects" class="column">
            <button class="nav-btn" data-effect="st-effect-4"></button>
        </div>
        <div class="name">
            <a href="/" class="button">
                <img src="/static/images/coffee.svg"/>
    """+name+"""
            </a>
        </div>
        <ul class="nav cl-effect-1">
            <li class="button">
                <a href="/americano" class="button">Americano</a>
            </li>
            <li class="button">
                <a href="/blog" class="button">Blog</a>
            </li>
            <li class="button">
                <a href="/work" class="button">What I Do</a>
            </li>
        </ul>
    </div>"""
    Html_file= open("templates/admin/header.html","w")
    Html_file.write(htmlStrad)
    Html_file.close()
