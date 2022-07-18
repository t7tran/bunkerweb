from Test import Test
from os.path import isdir, join, isfile
from os import chown, walk, getenv, listdir, mkdir
from shutil import copytree, rmtree
from traceback import format_exc
from subprocess import run
from time import sleep
from logger import log

class LinuxTest(Test) :

    def __init__(self, name, timeout, tests, distro) :
        super().__init__(name, "linux", timeout, tests)
        self._domains = {
            r"www\.example\.com": getenv("TEST_DOMAIN1"),
            r"auth\.example\.com": getenv("TEST_DOMAIN1"),
            r"app1\.example\.com": getenv("TEST_DOMAIN1_1"),
            r"app2\.example\.com": getenv("TEST_DOMAIN1_2"),
            r"app3\.example\.com": getenv("TEST_DOMAIN1_3")
        }
        if not distro in ["ubuntu", "debian", "fedora", "centos"] :
            raise(Exceptions("unknown distro " + distro))
        self.__distro = distro

    def init() :
        try :
            if not Test.init() :
                return False
            # TODO : find the nginx uid/gid on Docker images
            proc = run("sudo chown -R root:root /tmp/bw-data", shell=True)
            if proc.returncode != 0 :
                raise(Exception("chown failed (autoconf stack)"))
            if isdir("/tmp/linux")
                rmdir("/tmp/linux")
            mkdir("/tmp/linux")
            chmod("/tmp/linux", 0o0777)
            cmd = "docker run -v /tmp/bw-data/letsencrypt:/etc/letsencrypt -v /tmp/bw-data/cache:/opt/bunkerweb/cache -v /tmp/bw-data/configs:/opt/bunkerweb/configs -v /tmp/bw-data/www:/opt/bunkerweb/www -v /tmp/linux/variables.env:/opt/bunkerweb/variables.env -p 80:80 -p 443:443 --rm --name linux-" + self.__distro + " -d --tmpfs /tmp --tmpfs /run --tmpfs /run/lock -v /sys/fs/cgroup:/sys/fs/cgroup:ro bw-" + self.__distro
            proc = run(cmd, shell=True)
            if proc.returncode != 0 :
                raise(Exception("docker run failed (linux stack)"))
            cmd = "docker exec linux-" + self.__distro + " " 
            if self.__distro in ["ubuntu", "debian"] :
                cmd += " apt install -y /opt/*.deb"
            elif self.__distro in ["centos", "fedora"] :
                cmd += " dnf install -y /opt/*.rpm"
            proc = run(cmd, shell=True)
            if proc.returncode != 0 :
                raise(Exception("docker exec apt install failed (linux stack)"))
            proc = run("systemctl start bunkerweb", shell=True)
            if proc.returncode != 0 :
                raise(Exception("docker exec systemctl start failed (linux stack)"))
        except :
            log("LINUX", "❌", "exception while running LinuxTest.init()\n" + format_exc())
            return False
        return True

    def end() :
        ret = True
        try :
            if not Test.end() :
                return False
            proc = run("docker kill linux-" + self.__distro, shell=True)
            if proc.returncode != 0 :
                ret = False
        except :
            log("LINUX", "❌", "exception while running LinuxTest.end()\n" + format_exc())
            return False
        return ret

    def _setup_test(self) :
        try :
            super()._setup_test()
            test = "/tmp/tests/" + self._name
            example_data = "./examples/" + self._name + "/bw-data"
            for ex_domain, test_domain in self._domains.items() :
                Test.replace_in_files(test, ex_domain, test_domain)
                Test.rename(test, ex_domain, test_domain)
            Test.replace_in_files(test, "example.com", getenv("ROOT_DOMAIN"))
            setup = test + "/setup-linux.sh"
            if isfile(setup) :
                proc = run("sudo ./setup-linux.sh", cwd=test, shell=True)
                if proc.returncode != 0 :
                    raise(Exception("setup-linux failed"))
            if isdir(example_data) :
                for cp_dir in listdir(example_data) :
                    if isdir(join(example_data, cp_dir)) :
                        copytree(join(example_data, cp_dir), join("/tmp/bw-data", cp_dir))
            proc = run("systemctl restart bunkerweb", shell=True)
            if proc.returncode != 0 :
                raise(Exception("docker exec systemctl restart failed (linux stack)"))
        except :
            log("LINUX", "❌", "exception while running LinuxTest._setup_test()\n" + format_exc())
            self._cleanup_test()
            return False
        return True

    # def _cleanup_test(self) :
        # try :
            # super()._cleanup_test()
        # except :
            # log("AUTOCONF", "❌", "exception while running AutoconfTest._cleanup_test()\n" + format_exc())
            # return False
        # return True

    # def _debug_fail(self) :
        # cmd = "cat /var/log/nginx/access.log ;"
        # proc = run("docker-compose logs", shell=True, cwd=autoconf)
        # test = "/tmp/tests/" + self._name
        # proc = run("docker-compose -f autoconf.yml logs", shell=True, cwd=test)