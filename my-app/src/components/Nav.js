import React from "react";
import {
  SquareMenu,
  CircleUser,
  Settings,
  LogOut,
  MessageCircleMore,
} from "lucide-react";

import {
  Menu,
  MenuButton,
  IconButton,
  MenuList,
  MenuItem,
} from "@chakra-ui/react";

const Nav = ({ setView, user, client }) => {
  if (!user) {
    return null;
  }

  const logout = (e) => {
    client.logout().then(() => setView("login"));
  };

  return (
    <Menu>
      <MenuButton
        as={IconButton}
        aria-label="Options"
        icon={<SquareMenu />}
        variant="outline"
        size={"lg"}
      />
      <MenuList>
        <MenuItem disabled={true} icon={<CircleUser />}>
          {user.name}
        </MenuItem>
        {user.role === "admin" ? (
          <>
            <MenuItem
              icon={<MessageCircleMore />}
              onClick={() => setView("interpreter")}
            >
              Interpeter
            </MenuItem>

            <MenuItem
              icon={<Settings />}
              onClick={() => setView("control_panel")}
            >
              Control Panel
            </MenuItem>
          </>
        ) : null}
        <MenuItem icon={<LogOut />} onClick={logout}>
          Logout
        </MenuItem>
      </MenuList>
    </Menu>
  );
};

export default Nav;
